"""
Módulo para cargar modelos de predicción y procesar transacciones.

Este módulo utiliza modelos de machine learning para generar predicciones
sobre transacciones. Se emplean tanto modelos tradicionales (cargados con joblib)
como un modelo Keras, que se compila al cargar.
"""

import logging
import numpy as np
import pandas as pd
import joblib
from tensorflow.keras.models import load_model
from tensorflow.keras.optimizers import Adam
from sklearn.preprocessing import RobustScaler

logger = logging.getLogger(__name__)

# Escaladores globales para normalizar los datos
scaler_amount = RobustScaler()
scaler_time = RobustScaler()


def load_models():
    """
    Carga y compila los modelos de predicción desde archivos.

    Los modelos cargados son:
      - 'logistic': Modelo de regresión logística.
      - 'kneighbors': Modelo de k-vecinos.
      - 'svc': Modelo de Support Vector Classifier.
      - 'tree': Modelo de árbol de decisión.
      - 'keras': Modelo Keras compilado.

    Returns:
        dict: Diccionario con los modelos cargados.

    Raises:
        Exception: Si ocurre un error al cargar alguno de los modelos.
    """
    models = {}
    try:
        models['logistic'] = joblib.load('/app/model/logistic_regression_model.pkl')
        models['kneighbors'] = joblib.load('/app/model/knears_neighbors_model.pkl')
        models['svc'] = joblib.load('/app/model/svc_model.pkl')
        models['tree'] = joblib.load('/app/model/decision_tree_model.pkl')
        keras_model = load_model('/app/model/undersample_model.h5')
        keras_model.compile(optimizer=Adam(),
                            loss='categorical_crossentropy',
                            metrics=['accuracy'])
        models['keras'] = keras_model
        logger.info("Modelos cargados exitosamente.")
    except Exception as e:
        logger.error(f"Error cargando modelos: {str(e)}")
        raise e
    return models


def process_transaction(transaction_data, models):
    """
    Procesa los datos de una transacción para generar predicciones de fraude.

    Realiza las siguientes operaciones:
      - Convierte la entrada en un DataFrame.
      - Convierte los nombres de columnas a minúsculas.
      - Verifica y asigna valores por defecto a las columnas 'amount' y 'time'.
      - Convierte 'amount' a numérico y escala 'amount' y 'time'.
      - Ordena las columnas de forma que coincidan con el formato esperado.
      - Genera predicciones utilizando cada modelo cargado.

    Args:
        transaction_data (dict): Diccionario con los datos de la transacción.
        models (dict): Diccionario con los modelos de predicción.

    Returns:
        dict: Diccionario con las predicciones generadas. La estructura es:
            {
                'logistic': [probabilidad_no_fraude, probabilidad_fraude],
                'kneighbors': [probabilidad_no_fraude, probabilidad_fraude],
                'svc': {'non_fraud': probabilidad_no_fraude, 'fraud': probabilidad_fraude},
                'tree': [probabilidad_no_fraude, probabilidad_fraude],
                'keras': {'non_fraud': probabilidad_no_fraude, 'fraud': probabilidad_fraude}
            }

    Raises:
        Exception: Si ocurre un error durante el procesamiento o la predicción.
    """
    predictions = {}
    try:
        # Convertir la entrada en un DataFrame
        input_data = pd.DataFrame([transaction_data])

        # Loguear las columnas originales
        logger.info("Columnas originales: %s", input_data.columns.tolist())
        print("Columnas originales:", input_data.columns.tolist())

        # Convertir todas las columnas a minúsculas para uniformidad
        input_data.columns = [col.lower() for col in input_data.columns]
        logger.info("Columnas tras convertir a minúsculas: %s", input_data.columns.tolist())
        print("Columnas tras lower():", input_data.columns.tolist())

        # Verificar si la columna 'amount' está presente; de lo contrario, asignar valor por defecto
        if 'amount' not in input_data.columns:
            logger.warning("No se encontró la columna 'amount'. Las columnas disponibles son: %s",
                           input_data.columns.tolist())
            print("No se encontró 'amount'. Asignando valor por defecto 0.")
            input_data['amount'] = 0

        # Si no existe la columna 'time', asignar un valor por defecto (0)
        if 'time' not in input_data.columns:
            logger.info("No se encontró la columna 'time'. Asignando valor por defecto 0.")
            print("No se encontró 'time'. Asignando valor 0.")
            input_data['time'] = 0

        # Loguear el DataFrame antes de la conversión a numérico
        logger.info("DataFrame antes de conversión:\n%s", input_data)
        print("DataFrame antes de conversión:\n", input_data)

        # Convertir la columna 'amount' a numérico en caso de que venga como string
        input_data['amount'] = pd.to_numeric(input_data['amount'], errors='coerce')

        # Escalar las columnas 'amount' y 'time'
        input_data['scaled_amount'] = scaler_amount.fit_transform(input_data[['amount']])
        input_data['scaled_time'] = scaler_time.fit_transform(input_data[['time']])

        # Eliminar las columnas originales
        input_data = input_data.drop(['amount', 'time'], axis=1)

        # Ordenar las columnas según lo esperado: primero 'scaled_amount' y 'scaled_time' y luego 'v1' a 'v28'
        expected_columns = ['scaled_amount', 'scaled_time'] + [f'v{i}' for i in range(1, 29)]
        input_data = input_data[expected_columns]

        logger.info("DataFrame final con columnas ordenadas:\n%s", input_data)
        print("DataFrame final:\n", input_data)

        # Convertir a array de numpy
        input_array = input_data.values

        # Realizar predicciones con cada modelo
        logistic_reg_pred = models['logistic'].predict_proba(input_array)
        kneighbors_pred = models['kneighbors'].predict_proba(input_array)
        svc_pred = models['svc'].decision_function(input_array)
        svc_fraud_prob = 1 / (1 + np.exp(-svc_pred))
        svc_non_fraud_prob = 1 - svc_fraud_prob
        tree_pred = models['tree'].predict_proba(input_array)
        keras_pred = models['keras'].predict(input_array)

        predictions['logistic'] = [
            float(logistic_reg_pred[0][0]), float(logistic_reg_pred[0][1])
        ]
        predictions['kneighbors'] = [
            float(kneighbors_pred[0][0]), float(kneighbors_pred[0][1])
        ]
        predictions['svc'] = {
            'non_fraud': float(svc_non_fraud_prob[0]),
            'fraud': float(svc_fraud_prob[0])
        }
        predictions['tree'] = [
            float(tree_pred[0][0]), float(tree_pred[0][1])
        ]
        predictions['keras'] = {
            'non_fraud': float(keras_pred[0][0]),
            'fraud': float(keras_pred[0][1])
        }

        logger.info("Predicciones generadas: %s", predictions)
        print("Predicciones generadas:", predictions)
    except Exception as e:
        logger.error("Error en el procesamiento de la transacción: %s", str(e))
        print("Error en el procesamiento de la transacción:", str(e))
        raise e
    return predictions
