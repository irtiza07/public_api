import json
import logging
import redis
from confluent_kafka import Consumer, KafkaError, KafkaException, Producer
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage
from dotenv import load_dotenv
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Kafka configuration
kafka_config = {
    "bootstrap.servers": "localhost:29092",
    "group.id": "llm-processor-group",  # Required setting for Consumer - was missing
    "auto.offset.reset": "earliest",  # Start from the beginning if no offset is stored
    "socket.timeout.ms": 10000,  # Increase timeout for troubleshooting
    "request.timeout.ms": 20000,
}

# Redis configuration based on your Docker settings
redis_config = {
    "host": "localhost",
    "port": 6379,
    "password": "docker",
    "db": 0,
    "decode_responses": True,  # Automatically decode response bytes to strings
}

# Load environment variables
load_dotenv()

# Initialize LLM
llm = ChatOpenAI(
    model="gpt-3.5-turbo", temperature=0.7, api_key=os.getenv("OPENAI_API_KEY")
)

# Initialize Kafka producer
producer = Producer(kafka_config)


def connect_to_redis():
    """
    Connect to Redis instance
    """
    try:
        client = redis.Redis(**redis_config)
        # Test connection
        client.ping()
        logger.info("Connected to Redis successfully")
        return client
    except redis.RedisError as e:
        logger.error(f"Failed to connect to Redis: {e}")
        raise


def process_message(message, redis_client):
    """
    Process a Kafka message, call the LLM for an answer, store it in Redis, and publish the result back to Kafka
    """
    try:
        # Decode message value
        message_value = message.value().decode("utf-8")
        payload = json.loads(message_value)

        # Log the payload
        logger.info(f"Received message: {payload}")

        # Get conversation ID (used as Redis key)
        conversation_id = payload.get("conversation_id")
        prompt = payload.get("prompt")

        # Call the LLM to get the answer
        messages = [HumanMessage(content=prompt)]
        response = llm.invoke(messages)
        llm_answer = response.content

        # Store the question and answer in Redis
        cache_key = f"conversation:{conversation_id}"
        redis_client.lpush(
            cache_key,
            json.dumps(
                {
                    "question": prompt,
                    "answer": llm_answer,
                }
            ),
        )

        logger.info(f"Stored message in Redis with key: {cache_key}")
        logger.info(
            f"Full payload stored in Redis: {json.dumps({'question': prompt, 'answer': llm_answer})}"
        )

        # Publish the payload back to Kafka
        kafka_payload = {
            "conversation_id": conversation_id,
            "user_prompt": prompt,
            "llm_response": llm_answer,
        }
        producer.produce(
            topic="async_llm_response",
            key=conversation_id,
            value=json.dumps(kafka_payload),
            callback=lambda err, msg: logger.info(f"Message published successfully: {msg.topic()} [{msg.partition()}] at offset {msg.offset()} with payload: {json.dumps(kafka_payload)}" if err is None else f"Failed to publish message: {err}")
        )
        producer.flush()

    except Exception as e:
        logger.error(f"Error processing message: {e}")


def consume_messages(topic_name):
    """
    Consume messages from Kafka topic and store in Redis
    """
    # Connect to Redis
    redis_client = connect_to_redis()

    # Create consumer
    consumer = Consumer(kafka_config)

    try:
        # Subscribe to topic
        consumer.subscribe([topic_name])
        logger.info(f"Subscribed to topic: {topic_name}")

        # Consume messages
        while True:
            message = consumer.poll(timeout=1.0)
            if message is None:
                continue

            process_message(message, redis_client)

    except KeyboardInterrupt:
        logger.info("Consumer stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        # Close consumer
        consumer.close()


def main():
    topic_name = "async_user_prompt"
    consume_messages(topic_name)


if __name__ == "__main__":
    main()
