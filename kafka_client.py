from confluent_kafka import Producer, Consumer, KafkaException
import logging
from config import Config

logger = logging.getLogger(__name__)


def create_producer():
    """
    Crea y retorna un productor de Kafka.

    Configura el productor utilizando los parámetros definidos en Config y,
    en caso de éxito, retorna una instancia de Producer.

    Returns:
        Producer: Instancia de Producer configurada.
        None: Si ocurre un error durante la creación del productor.
    """
    conf = {
        'bootstrap.servers': Config.KAFKA_BOOTSTRAP_SERVERS,
        'security.protocol': Config.KAFKA_SECURITY_PROTOCOL,
        'sasl.mechanisms': Config.KAFKA_SASL_MECHANISMS,
        'sasl.username': Config.KAFKA_SASL_USERNAME,
        'sasl.password': Config.KAFKA_SASL_PASSWORD,
    }
    try:
        producer = Producer(conf)
        logger.info("Kafka Producer creado.")
        return producer
    except Exception as e:
        logger.error(f"Error creando Kafka Producer: {str(e)}")
        return None


def create_consumer(topic):
    """
    Crea y retorna un consumidor de Kafka suscrito a un tópico específico.

    Configura el consumidor utilizando los parámetros definidos en Config y
    se suscribe al tópico proporcionado.

    Args:
        topic (str): Nombre del tópico al cual el consumidor se suscribirá.

    Returns:
        Consumer: Instancia de Consumer configurada y suscrita al tópico.
        None: Si ocurre un error durante la creación del consumidor.
    """
    conf = {
        'bootstrap.servers': Config.KAFKA_BOOTSTRAP_SERVERS,
        'group.id': 'transactions-group-1',
        'auto.offset.reset': 'earliest',
        'security.protocol': Config.KAFKA_SECURITY_PROTOCOL,
        'sasl.mechanisms': Config.KAFKA_SASL_MECHANISMS,
        'sasl.username': Config.KAFKA_SASL_USERNAME,
        'sasl.password': Config.KAFKA_SASL_PASSWORD,
    }
    try:
        consumer = Consumer(conf)
        consumer.subscribe([topic])
        logger.info(f"Kafka Consumer suscrito al tópico {topic}.")
        return consumer
    except Exception as e:
        logger.error(f"Error creando Kafka Consumer: {str(e)}")
        return None


def send_to_topic(producer, topic, key, value):
    """
    Envía un mensaje a un tópico de Kafka utilizando el productor proporcionado.

    Args:
        producer (Producer): Instancia de Kafka Producer.
        topic (str): Nombre del tópico al cual se enviará el mensaje.
        key (str): Clave del mensaje.
        value (str): Valor o contenido del mensaje.

    Registra en el log el éxito o fallo del envío del mensaje.
    """
    try:
        producer.produce(topic, key=key, value=value)
        producer.flush()
        logger.info(f"Mensaje enviado al tópico {topic}.")
    except Exception as e:
        logger.error(f"Error enviando mensaje al tópico {topic}: {str(e)}")
