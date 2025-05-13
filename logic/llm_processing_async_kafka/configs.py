import redis
from confluent_kafka import Producer, KafkaException
from confluent_kafka.admin import AdminClient, NewTopic
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

kafka_topic_name = "async-llm-processing"

# Kafka Producer configuration
kafka_producer_config = {
    "bootstrap.servers": "localhost:29092",
    "client.id": "python-producer",
    "socket.timeout.ms": 10000,  # Increase timeout for troubleshooting
    "request.timeout.ms": 20000,
}

# Kafka Consumer configuration
kafka_consumer_config = {
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


def create_topic(topic_name, num_partitions=1, replication_factor=1):
    """
    Create a Kafka topic if it doesn't exist
    """
    admin_client = AdminClient(kafka_producer_config)

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


def create_topic(topic_name, num_partitions=1, replication_factor=1):
    """
    Create a Kafka topic if it doesn't exist
    """
    admin_client = AdminClient(kafka_producer_config)

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