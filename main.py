"""
Aplicación FastAPI para consumir, procesar y almacenar transacciones.
Integra Kafka para la mensajería y NeonDB (PostgreSQL) para el almacenamiento.
Los modelos de predicción se cargan al iniciar la aplicación.
"""

import asyncio
import json
import logging
import os

from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict

try:
    from kafka_client import create_consumer, create_producer, send_to_topic
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False
    logger.warning("Kafka no disponible - funcionando sin Kafka")

try:
    from db import store_transaction, init_transactions_table, get_transaction
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False
    logger.warning("Base de datos no disponible - funcionando sin DB")

from prediction import load_models, process_transaction
from config import Config

logger = logging.getLogger(__name__)
app = FastAPI(title="Fraud Detection API", description="API para detección de fraude en transacciones", version="1.0.0")

# Configurar CORS para permitir conexiones desde Streamlit
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelos Pydantic para validación de datos
class TransactionInput(BaseModel):
    time: float
    amount: float
    v1: float
    v2: float
    v3: float
    v4: float
    v5: float
    v6: float
    v7: float
    v8: float
    v9: float
    v10: float
    v11: float
    v12: float
    v13: float
    v14: float
    v15: float
    v16: float
    v17: float
    v18: float
    v19: float
    v20: float
    v21: float
    v22: float
    v23: float
    v24: float
    v25: float
    v26: float
    v27: float
    v28: float

class PredictionResponse(BaseModel):
    is_fraud: bool
    fraud_probability: float
    models_predictions: Dict
    transaction_id: str = None

# Inicializar la tabla en NeonDB (solo si está disponible)
if DB_AVAILABLE:
    try:
        init_transactions_table()
        logger.info("Base de datos inicializada correctamente")
    except Exception as e:
        logger.warning(f"No se pudo conectar a la base de datos: {e}")
        DB_AVAILABLE = False

# Cargar modelos al iniciar la aplicación
models = load_models()

# Crear clientes Kafka (solo si está disponible)
if KAFKA_AVAILABLE:
    try:
        producer = create_producer()
        consumer = create_consumer(Config.KAFKA_TOPIC_INPUT)
        logger.info("Kafka inicializado correctamente")
    except Exception as e:
        logger.warning(f"No se pudo conectar a Kafka: {e}")
        KAFKA_AVAILABLE = False
        producer = None
        consumer = None
else:
    producer = None
    consumer = None


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


@app.get("/")
def root():
    """
    Endpoint raíz del API.
    
    Returns:
        dict: Información básica del API
    """
    return {
        "message": "Sistema de Detección de Fraude API",
        "autor": "Santiago Prado",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "predict": "/predict",
            "docs": "/docs"
        }
    }


@app.post("/predict", response_model=PredictionResponse)
async def predict_transaction(transaction: TransactionInput):
    """
    Predice si una transacción es fraudulenta.
    
    Args:
        transaction (TransactionInput): Datos de la transacción a analizar
        
    Returns:
        PredictionResponse: Resultado de la predicción con probabilidades por modelo
    """
    try:
        # Convertir a diccionario para el procesamiento
        transaction_data = transaction.dict()
        
        # Procesar transacción con los modelos
        predictions = process_transaction(transaction_data, models)
        
        # Determinar si es fraude (usando promedio de modelos como ejemplo)
        # Puedes ajustar esta lógica según tus necesidades
        fraud_probs = [
            predictions['logistic'][1],
            predictions['kneighbors'][1], 
            predictions['svc']['fraud'] if isinstance(predictions['svc'], dict) else predictions['svc'][1],
            predictions['tree'][1]
        ]
        
        avg_fraud_prob = sum(fraud_probs) / len(fraud_probs)
        is_fraud = avg_fraud_prob > 0.5
        
        # Almacenar en DB solo si está disponible
        if DB_AVAILABLE:
            try:
                store_transaction(json.dumps(transaction_data), predictions)
            except Exception as e:
                logger.warning(f"No se pudo almacenar en DB: {e}")
        
        # Enviar a Kafka solo si está disponible
        if KAFKA_AVAILABLE and producer:
            try:
                send_to_topic(
                    producer,
                    Config.KAFKA_TOPIC_OUTPUT,
                    key=f"pred_{hash(str(transaction_data))}",
                    value=json.dumps(predictions)
                )
            except Exception as e:
                logger.warning(f"No se pudo enviar a Kafka: {e}")

        return PredictionResponse(
            is_fraud=is_fraud,
            fraud_probability=avg_fraud_prob,
            models_predictions=predictions
        )
        
    except Exception as e:
        logger.error(f"Error en predicción: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error en el procesamiento: {str(e)}")


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
    return {
        "status": "ok",
        "nombre": "Santiago Prado",
        "models_loaded": len(models) > 0,
        "models_count": len(models),
        "kafka_available": KAFKA_AVAILABLE,
        "db_available": DB_AVAILABLE,
        "environment": os.getenv("ENVIRONMENT", "unknown")
    }


@app.get("/transaction/{transaction_id}")
def get_transaction_result(transaction_id: str):
    """
    Obtiene el resultado de una transacción procesada.

    Args:
        transaction_id (str): Identificador de la transacción.

    Returns:
        dict: Contiene el identificador y el estado.

    Raises:
        HTTPException: Si la base de datos no está disponible o no se encuentra la transacción.
    """
    if not DB_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Base de datos no disponible. Use el endpoint /predict para predicciones directas."
        )
    
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

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
