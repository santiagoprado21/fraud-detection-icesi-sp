"""
Aplicación FastAPI para consumir, procesar y almacenar transacciones.
Integra Kafka para la mensajería y NeonDB (PostgreSQL) para el almacenamiento.
Los modelos de predicción se cargan al iniciar la aplicación.
"""

import asyncio
import json
import logging

from fastapi import FastAPI, BackgroundTasks, HTTPException

from kafka_client import create_consumer, create_producer, send_to_topic
from prediction import load_models, process_transaction
from db import store_transaction, init_transactions_table, get_transaction
from config import Config

logger = logging.getLogger(__name__)
app = FastAPI()

# Inicializar la tabla en NeonDB
init_transactions_table()

# Cargar modelos al iniciar la aplicación
models = load_models()

# Crear clientes Kafka
producer = create_producer()
consumer = create_consumer(Config.KAFKA_TOPIC_INPUT)


async def consume_transactions():
    """
    Consume transacciones de Kafka de manera continua.

    Esta función realiza un 'polling' en el consumidor de Kafka para obtener mensajes,
    procesa cada transacción (aplicando los modelos de predicción), almacena el resultado
    en NeonDB y envía las predicciones a un tópico de salida en Kafka.
    """
    while True:
        msg = consumer.poll(timeout=1.0)
        if msg is None:
            await asyncio.sleep(1)
            continue

        if msg.error():
            logger.error(f"Error en Kafka Consumer: {msg.error()}")
            print("Error en Kafka Consumer:", msg.error())
            continue

        try:
            transaction_data = json.loads(msg.value().decode('utf-8'))
            logger.info(f"Transacción recibida: {transaction_data}")
            print("Transacción recibida:", transaction_data)

            # Procesar la transacción (predecir, almacenar, etc.)
            predictions = process_transaction(transaction_data, models)
            store_transaction(json.dumps(transaction_data), predictions)
            send_to_topic(
                producer,
                Config.KAFKA_TOPIC_OUTPUT,
                key=transaction_data.get("transaction_id", ""),
                value=json.dumps(predictions)
            )
        except Exception as e:
            logger.error(f"Error procesando transacción: {str(e)}")
            print("Error procesando transacción:", str(e))

        await asyncio.sleep(0.1)


@app.get("/start-consuming")
async def start_consuming(background_tasks: BackgroundTasks):
    """
    Inicia el consumo de transacciones en segundo plano.

    Esta ruta agrega la tarea asíncrona `consume_transactions` a las tareas en segundo
    plano de FastAPI, permitiendo procesar las transacciones sin bloquear las demás rutas.

    Args:
        background_tasks (BackgroundTasks): Tareas en segundo plano de FastAPI.

    Returns:
        dict: Mensaje de confirmación indicando que el consumo ha comenzado.
    """
    background_tasks.add_task(consume_transactions)
    return {"message": "Consumiendo transacciones en segundo plano."}


@app.get("/health")
def health():
    """
    Verifica el estado de la aplicación.

    Returns:
        dict: Estado de la aplicación.
    """
    return {"status": "ok"}


@app.get("/transaction/{transaction_id}")
def get_transaction_result(transaction_id: str):
    """
    Obtiene el resultado de una transacción procesada.

    Consulta la transacción en NeonDB utilizando el `transaction_id`. Se evalúa la predicción
    del modelo 'kneighbors' para determinar si la transacción es fraude o aprobada.

    Args:
        transaction_id (str): Identificador de la transacción.

    Returns:
        dict: Contiene el identificador, el estado (fraude, aprobada o sin resultado) y
              los detalles completos de la transacción.

    Raises:
        HTTPException: Si no se encuentra la transacción o aún está en proceso.
    """
    # Consulta la transacción en la base de datos (NeonDB)
    transaction = get_transaction(transaction_id)
    if transaction is None:
        raise HTTPException(
            status_code=404,
            detail="Transacción no encontrada o aún en proceso."
        )

    # Se asume que la predicción del modelo 'kneighbors' se utiliza para decidir
    kneighbors = transaction.get("kneighbors")
    if kneighbors is not None:
        # Si el valor de no fraude es mayor que el de fraude, se considera aprobada
        if float(kneighbors[0]) > float(kneighbors[1]):
            result = "fraude"
        else:
            result = "aprobada"
    else:
        result = "sin resultado"

    return {
        "transaction_id": transaction_id,
        "status": result,
        "details": transaction
    }
