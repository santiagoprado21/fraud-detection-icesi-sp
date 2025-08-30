import psycopg2
import logging
from config import Config

logger = logging.getLogger(__name__)


def get_db_connection():
    """
    Establece y retorna una conexión a la base de datos NeonDB (PostgreSQL).

    Returns:
        connection (psycopg2.extensions.connection): Conexión establecida a la base de datos.

    Raises:
        Exception: Si ocurre algún error al conectar a la base de datos.
    """
    try:
        conn = psycopg2.connect(Config.DATABASE_URL)
        logger.info("Conectado a NeonDB (PostgreSQL).")
        return conn
    except Exception as e:
        logger.error(f"Error conectando a NeonDB: {str(e)}")
        raise


def init_transactions_table():
    """
    Crea la tabla 'transactions' en NeonDB si no existe.

    La tabla contiene los siguientes campos:
        - id: Identificador único autoincrementable.
        - transaction_json: Datos de la transacción en formato JSONB.
        - logistic_regression_fraud: Probabilidad de fraude según regresión logística.
        - logistic_regression_non_fraud: Probabilidad de no fraude según regresión logística.
        - kneighbors_fraud: Probabilidad de fraude según k-vecinos.
        - kneighbors_non_fraud: Probabilidad de no fraude según k-vecinos.
        - svc_fraud: Probabilidad de fraude según SVC.
        - svc_non_fraud: Probabilidad de no fraude según SVC.
        - decision_tree_fraud: Probabilidad de fraude según árbol de decisión.
        - decision_tree_non_fraud: Probabilidad de no fraude según árbol de decisión.
        - keras_fraud: Probabilidad de fraude según modelo Keras.
        - keras_non_fraud: Probabilidad de no fraude según modelo Keras.

    Registra en el log la creación o verificación de la tabla.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id SERIAL PRIMARY KEY,
                transaction_json JSONB,
                logistic_regression_fraud REAL,
                logistic_regression_non_fraud REAL,
                kneighbors_fraud REAL,
                kneighbors_non_fraud REAL,
                svc_fraud REAL,
                svc_non_fraud REAL,
                decision_tree_fraud REAL,
                decision_tree_non_fraud REAL,
                keras_fraud REAL,
                keras_non_fraud REAL
            )
        """)
        conn.commit()
        logger.info("Tabla 'transactions' creada o verificada en NeonDB.")
    except Exception as e:
        conn.rollback()
        logger.error(f"Error al crear la tabla en NeonDB: {str(e)}")
    finally:
        cursor.close()
        conn.close()


def store_transaction(transaction_json, predictions):
    """
    Almacena una transacción y sus predicciones en la tabla 'transactions' de NeonDB.

    Args:
        transaction_json (dict): Datos de la transacción en formato JSON.
        predictions (dict): Diccionario con las predicciones de los modelos. Estructura esperada:
            {
                'logistic': [valor_no_fraude, valor_fraude],
                'kneighbors': [valor_no_fraude, valor_fraude],
                'svc': {'fraud': valor_fraude, 'non_fraud': valor_no_fraude},
                'tree': [valor_no_fraude, valor_fraude],
                'keras': {'fraud': valor_fraude, 'non_fraud': valor_no_fraude}
            }

    Registra en el log el éxito o error al almacenar la transacción.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO transactions (
                transaction_json,
                logistic_regression_fraud, logistic_regression_non_fraud,
                kneighbors_fraud, kneighbors_non_fraud,
                svc_fraud, svc_non_fraud,
                decision_tree_fraud, decision_tree_non_fraud,
                keras_fraud, keras_non_fraud
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            transaction_json,
            predictions['logistic'][1], predictions['logistic'][0],
            predictions['kneighbors'][1], predictions['kneighbors'][0],
            predictions['svc']['fraud'], predictions['svc']['non_fraud'],
            predictions['tree'][1], predictions['tree'][0],
            predictions['keras']['fraud'], predictions['keras']['non_fraud']
        ))
        conn.commit()
        logger.info("Transacción almacenada en NeonDB.")
    except Exception as e:
        conn.rollback()
        logger.error(f"Error almacenando la transacción: {str(e)}")
    finally:
        cursor.close()
        conn.close()


def get_transaction(transaction_id: str):
    """
    Obtiene la transacción más reciente que coincide con el ID de transacción.

    Se busca en la columna 'transaction_json' filtrando por el campo 'transaction_id'.

    Args:
        transaction_id (str): Identificador de la transacción a buscar.

    Returns:
        dict or None: Diccionario con los datos de la transacción y las predicciones,
                      o None si no se encuentra la transacción.

    La estructura del diccionario retornado es:
        {
            "transaction_json": <json>,
            "logistic": [valor_no_fraude, valor_fraude],
            "kneighbors": [valor_no_fraude, valor_fraude],
            "svc": {"non_fraud": valor_no_fraude, "fraud": valor_fraude},
            "tree": [valor_no_fraude, valor_fraude],
            "keras": {"non_fraud": valor_no_fraude, "fraud": valor_fraude}
        }
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        query = """
            SELECT 
                transaction_json,
                logistic_regression_fraud, logistic_regression_non_fraud,
                kneighbors_fraud, kneighbors_non_fraud,
                svc_fraud, svc_non_fraud,
                decision_tree_fraud, decision_tree_non_fraud,
                keras_fraud, keras_non_fraud
            FROM transactions
            WHERE transaction_json->>'transaction_id' = %s
            ORDER BY id DESC
            LIMIT 1;
        """
        cursor.execute(query, (transaction_id,))
        row = cursor.fetchone()
        logger.info("Resultado de get_transaction para %s: %s", transaction_id, row)
        if row is None:
            return None
        result = {
            "transaction_json": row[0],
            "logistic": [row[2], row[1]],  # [non_fraud, fraud]
            "kneighbors": [row[4], row[3]],
            "svc": {"non_fraud": row[6], "fraud": row[5]},
            "tree": [row[8], row[7]],
            "keras": {"non_fraud": row[10], "fraud": row[9]}
        }
        return result
    except Exception as e:
        logger.error("Error al obtener la transacción: %s", str(e))
        return None
    finally:
        cursor.close()
        conn.close()
