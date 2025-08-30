import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # NeonDB PostgreSQL
    DATABASE_URL = os.getenv("DATABASE_URL")

    # Kafka Confluent Cloud
    KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "pkc-p11xm.us-east-1.aws.confluent.cloud:9092")
    KAFKA_SASL_MECHANISMS = os.getenv("KAFKA_SASL_MECHANISMS", "PLAIN")
    KAFKA_SECURITY_PROTOCOL = os.getenv("KAFKA_SECURITY_PROTOCOL", "SASL_SSL")
    KAFKA_SASL_USERNAME = os.getenv("KAFKA_SASL_USERNAME")
    KAFKA_SASL_PASSWORD = os.getenv("KAFKA_SASL_PASSWORD")
    KAFKA_TOPIC_INPUT = os.getenv("KAFKA_TOPIC_INPUT", "transactions_stream")
    KAFKA_TOPIC_OUTPUT = os.getenv("KAFKA_TOPIC_OUTPUT", "fraud_predictions")
