import uuid
from confluent_kafka import Producer, KafkaException
from confluent_kafka.admin import AdminClient, NewTopic
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage
import json
import logging
import sys

from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Initialize LLM
llm = ChatOpenAI(
    model="gpt-3.5-turbo", temperature=0.7, api_key=os.getenv("OPENAI_API_KEY")
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Kafka configuration
# Note: Using the internal Docker network connection since we're getting connection refused on localhost
kafka_config = {
    "bootstrap.servers": "localhost:29092",
    "client.id": "python-producer",
    "socket.timeout.ms": 10000,  # Increase timeout for troubleshooting
    "request.timeout.ms": 20000,
}


def create_topic(topic_name, num_partitions=1, replication_factor=1):
    """
    Create a Kafka topic if it doesn't exist
    """
    admin_client = AdminClient(kafka_config)

    # Check if topic already exists
    metadata = admin_client.list_topics(timeout=10)
    if topic_name in metadata.topics:
        logger.info(f"Topic {topic_name} already exists")
        return

    # Create topic
    topic = NewTopic(
        topic_name, num_partitions=num_partitions, replication_factor=replication_factor
    )

    try:
        futures = admin_client.create_topics([topic])

        # Wait for topic creation
        for topic_name, future in futures.items():
            future.result()  # Blocks until topic is created
            logger.info(f"Topic {topic_name} created successfully")
    except KafkaException as e:
        logger.error(f"Failed to create topic {topic_name}: {e}")
        sys.exit(1)


def delivery_report(err, msg):
    """
    Callback function for message delivery reports
    """
    if err is not None:
        logger.error(f"Message delivery failed: {err}")
    else:
        logger.info(
            f"Message delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}"
        )


def publish_message(producer, topic, message):
    """
    Publish a message to a Kafka topic
    """
    try:
        # Convert dict to JSON string
        message_json = json.dumps(message)

        # Produce message
        producer.produce(
            topic=topic,
            key=str(message.get("conversation_id")),
            value=message_json,
            callback=delivery_report,
        )

        # Flush to ensure message is sent
        producer.flush()

    except Exception as e:
        logger.error(f"Failed to publish message: {e}")
        return False

    return True


def create_llm_message(prompt, conversation_id):
    """
    Create a message with the required fields
    """

    messages = [HumanMessage(content=prompt)]
    response = llm.invoke(messages)

    return {
        "conversation_id": conversation_id,
        "prompt": prompt,
        "llm_answer": response.content,
    }


def main():
    topic_name = "async_llm_response"
    create_topic(topic_name)

    producer = Producer(kafka_config)

    conversation_id = str(uuid.uuid4())
    while True:
        user_prompt = input("Enter your prompt: ")

        # Example of publishing a message
        message_to_publish = create_llm_message(
            prompt=user_prompt,
            conversation_id=conversation_id,
        )

        print(f"Publishing message: {message_to_publish}")
        publish_message(producer, topic_name, message_to_publish)

        logger.info("Messages published successfully")


if __name__ == "__main__":
    main()
