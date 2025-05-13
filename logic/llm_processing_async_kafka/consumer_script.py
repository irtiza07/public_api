import json
import logging
import redis
from confluent_kafka import Consumer, KafkaError, KafkaException

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
    Process a Kafka message and store it in Redis
    """
    try:
        # Decode message value
        message_value = message.value().decode("utf-8")
        payload = json.loads(message_value)

        # Log the payload
        logger.info(f"Received message: {payload}")

        # Get conversation ID (used as Redis key)
        conversation_id = payload.get("conversation_id")

        cache_key = f"conversation:{conversation_id}"

        redis_client.lpush(
            cache_key,
            json.dumps(
                {
                    "question": payload.get("prompt"),
                    "answer": payload.get("llm_answer"),
                }
            ),
        )

        logger.info(f"Stored message in Redis with key: {cache_key}")

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
    topic_name = "async-llm-processing"
    consume_messages(topic_name)


if __name__ == "__main__":
    main()
