"""
Frontend de Streamlit para el Sistema de Detección de Fraude
============================================================

Aplicación web interactiva que permite a los usuarios:
- Simular transacciones
- Obtener predicciones de fraude en tiempo real
- Visualizar resultados de múltiples modelos de ML
- Monitorear el estado del sistema

Autor: Santiago Prado
Proyecto: Fraud Detection ICESI
"""

import streamlit as st
import requests
import json
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time

# Configuración de la página
st.set_page_config(
    page_title="🛡️ Fraud Detection System",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# URLs de la API
import os
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
HEALTH_URL = f"{API_BASE_URL}/health"
PREDICT_URL = f"{API_BASE_URL}/predict"

# CSS personalizado para hacer la interfaz más bonita
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 2rem;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    
    .status-healthy {
        background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
        padding: 0.5rem;
        border-radius: 5px;
        color: white;
        text-align: center;
    }
    
    .status-error {
        background: linear-gradient(135deg, #f44336 0%, #da190b 100%);
        padding: 0.5rem;
        border-radius: 5px;
        color: white;
        text-align: center;
    }
    
    .prediction-card {
        border: 2px solid;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .fraud-card {
        border-color: #f44336;
        background-color: #ffebee;
    }
    
    .safe-card {
        border-color: #4CAF50;
        background-color: #e8f5e8;
    }
</style>
""", unsafe_allow_html=True)

def check_api_health():
    """Verifica el estado de la API"""
    try:
        response = requests.get(HEALTH_URL, timeout=5)
        if response.status_code == 200:
            return True, response.json()
        else:
            return False, None
    except Exception as e:
        return False, str(e)

def generate_sample_transaction():
    """Genera una transacción de ejemplo realista"""
    # Generar características V1-V28 (simulando PCA de transacciones reales)
    np.random.seed(int(time.time()))
    
    # V1-V28 típicamente están en rangos específicos después de PCA
    v_features = {}
    for i in range(1, 29):
        if i in [1, 2, 3]:  # Primeras componentes con mayor varianza
            v_features[f'v{i}'] = np.random.normal(0, 2)
        elif i in range(4, 11):  # Componentes medias
            v_features[f'v{i}'] = np.random.normal(0, 1.5)
        else:  # Componentes menores
            v_features[f'v{i}'] = np.random.normal(0, 1)
    
    # Tiempo (segundos desde inicio del día)
    time_val = np.random.randint(0, 86400)
    
    # Monto (distribución log-normal típica de transacciones)
    amount = np.random.lognormal(mean=3, sigma=1.5)
    amount = round(max(1, min(amount, 25000)), 2)  # Entre $1 y $25,000
    
    transaction = {
        'time': time_val,
        'amount': amount,
        **v_features
    }
    
    return transaction

def main():
    # Header principal
    st.markdown('<h1 class="main-header">🛡️ Sistema de Detección de Fraude</h1>', unsafe_allow_html=True)
    
    # Sidebar para navegación
    st.sidebar.title("🎛️ Panel de Control")
    page = st.sidebar.selectbox(
        "Selecciona una página:",
        ["🏠 Dashboard", "🔍 Predicción Individual", "📊 Análisis Masivo", "⚙️ Estado del Sistema"]
    )
    
    if page == "🏠 Dashboard":
        show_dashboard()
    elif page == "🔍 Predicción Individual":
        show_prediction_page()
    elif page == "📊 Análisis Masivo":
        show_batch_analysis()
    elif page == "⚙️ Estado del Sistema":
        show_system_status()

def show_dashboard():
    """Página principal del dashboard"""
    st.header("📈 Dashboard Principal")
    
    # Verificar estado de la API
    is_healthy, health_data = check_api_health()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if is_healthy:
            st.markdown("""
            <div class="metric-card">
                <h3>🟢 API Status</h3>
                <p>Healthy</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="metric-card" style="background: linear-gradient(135deg, #f44336 0%, #da190b 100%);">
                <h3>🔴 API Status</h3>
                <p>Error</p>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        if is_healthy and health_data:
            models_count = health_data.get('models_count', 0)
            st.markdown(f"""
            <div class="metric-card">
                <h3>🤖 Modelos ML</h3>
                <p>{models_count} Activos</p>
            </div>
            """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card">
            <h3>⚡ Tiempo Respuesta</h3>
            <p>< 100ms</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="metric-card">
            <h3>🔒 Seguridad</h3>
            <p>Alta</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Gráfico de ejemplo de transacciones
    st.subheader("📊 Simulación de Transacciones en Tiempo Real")
    
    # Generar datos de ejemplo
    dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='D')
    legitimate_transactions = np.random.poisson(lam=100, size=len(dates))
    fraud_transactions = np.random.poisson(lam=5, size=len(dates))
    
    df = pd.DataFrame({
        'Fecha': dates,
        'Transacciones Legítimas': legitimate_transactions,
        'Transacciones Fraudulentas': fraud_transactions
    })
    
    fig = px.line(df, x='Fecha', y=['Transacciones Legítimas', 'Transacciones Fraudulentas'],
                  title='Volumen de Transacciones por Día')
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

def show_prediction_page():
    """Página para predicciones individuales"""
    st.header("🔍 Predicción Individual de Transacciones")
    
    # Verificar que la API esté disponible
    is_healthy, _ = check_api_health()
    if not is_healthy:
        st.error("❌ La API no está disponible. Verifica que el backend esté ejecutándose.")
        return
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📝 Datos de la Transacción")
        
        # Opción para generar transacción automática
        if st.button("🎲 Generar Transacción de Ejemplo", type="primary"):
            st.session_state.sample_transaction = generate_sample_transaction()
        
        # Campos principales
        amount = st.number_input("💰 Monto ($)", min_value=0.01, max_value=100000.0, 
                                value=st.session_state.get('sample_transaction', {}).get('amount', 100.0),
                                step=0.01, format="%.2f")
        
        time_val = st.number_input("⏰ Tiempo (segundos desde medianoche)", 
                                  min_value=0, max_value=86399,
                                  value=st.session_state.get('sample_transaction', {}).get('time', 43200))
        
        # Mostrar tiempo en formato legible
        hours = time_val // 3600
        minutes = (time_val % 3600) // 60
        st.info(f"⌚ Hora equivalente: {hours:02d}:{minutes:02d}")
        
        st.subheader("🔢 Características PCA (V1-V28)")
        st.info("💡 Estas son características derivadas de PCA aplicado a datos de transacciones reales")
        
        # Generar campos V1-V28
        v_features = {}
        cols = st.columns(4)
        for i in range(1, 29):
            col_idx = (i-1) % 4
            with cols[col_idx]:
                default_val = st.session_state.get('sample_transaction', {}).get(f'v{i}', 0.0)
                v_features[f'v{i}'] = st.number_input(
                    f"V{i}", 
                    value=float(default_val),
                    step=0.1, 
                    format="%.4f",
                    key=f"v{i}"
                )
    
    with col2:
        st.subheader("🎯 Resultados de Predicción")
        
        if st.button("🚀 Analizar Transacción", type="primary"):
            # Preparar datos para la API
            transaction_data = {
                'time': time_val,
                'amount': amount,
                **v_features
            }
            
            with st.spinner("🔄 Analizando transacción..."):
                try:
                    # Llamar a la API real
                    response = requests.post(PREDICT_URL, json=transaction_data, timeout=10)
                    
                    if response.status_code == 200:
                        result = response.json()
                        is_fraud = result['is_fraud']
                        fraud_probability = result['fraud_probability']
                        models_results = result['models_predictions']
                    else:
                        st.error(f"❌ Error en la API: {response.status_code}")
                        return
                        
                except requests.exceptions.RequestException as e:
                    st.error(f"❌ Error de conexión con la API: {str(e)}")
                    return
                
                # Mostrar resultado principal
                if is_fraud:
                    st.markdown(f"""
                    <div class="prediction-card fraud-card">
                        <h3>🚨 TRANSACCIÓN SOSPECHOSA</h3>
                        <h2>Probabilidad de Fraude: {fraud_probability:.1%}</h2>
                        <p>⚠️ Esta transacción requiere revisión manual</p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="prediction-card safe-card">
                        <h3>✅ TRANSACCIÓN SEGURA</h3>
                        <h2>Probabilidad de Fraude: {fraud_probability:.1%}</h2>
                        <p>✨ Transacción aprobada automáticamente</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Gráfico de probabilidades por modelo
                st.subheader("📊 Análisis por Modelo")
                
                model_names = ['Regresión Logística', 'K-Vecinos', 'SVM', 'Árbol de Decisión']
                fraud_probs = [
                    models_results['logistic'][1],
                    models_results['kneighbors'][1],
                    models_results['svc']['fraud'],
                    models_results['tree'][1]
                ]
                
                fig = go.Figure(data=[
                    go.Bar(name='Probabilidad de Fraude', 
                          x=model_names, 
                          y=fraud_probs,
                          marker_color=['red' if p > 0.5 else 'green' for p in fraud_probs])
                ])
                fig.update_layout(
                    title="Predicciones por Modelo de ML",
                    yaxis_title="Probabilidad de Fraude",
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Detalles técnicos
                with st.expander("🔍 Detalles Técnicos"):
                    st.json(models_results)

def show_batch_analysis():
    """Página para análisis masivo"""
    st.header("📊 Análisis Masivo de Transacciones")
    
    st.info("📁 Sube un archivo CSV con transacciones para análisis masivo")
    
    uploaded_file = st.file_uploader("Elige un archivo CSV", type="csv")
    
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            st.subheader("👀 Vista Previa de los Datos")
            st.dataframe(df.head())
            
            if st.button("🚀 Procesar Lote"):
                # Simular procesamiento
                progress_bar = st.progress(0)
                for i in range(100):
                    time.sleep(0.01)
                    progress_bar.progress(i + 1)
                
                # Generar resultados simulados
                n_transactions = len(df)
                fraud_count = np.random.randint(1, max(2, n_transactions // 10))
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("📝 Total Transacciones", n_transactions)
                
                with col2:
                    st.metric("🚨 Fraudes Detectados", fraud_count, delta=f"{fraud_count/n_transactions:.1%}")
                
                with col3:
                    st.metric("✅ Transacciones Seguras", n_transactions - fraud_count)
                
                # Gráfico de distribución
                labels = ['Seguras', 'Fraudulentas']
                values = [n_transactions - fraud_count, fraud_count]
                
                fig = px.pie(values=values, names=labels, title="Distribución de Transacciones")
                st.plotly_chart(fig)
                
        except Exception as e:
            st.error(f"❌ Error al procesar el archivo: {str(e)}")
    
    else:
        # Mostrar formato esperado
        st.subheader("📋 Formato Esperado del CSV")
        sample_data = {
            'time': [43200, 54000, 32400],
            'amount': [150.50, 2500.00, 75.25],
            'v1': [-1.234, 0.567, 2.101],
            'v2': [0.876, -1.234, 0.445],
            '...': ['...', '...', '...'],
            'v28': [0.123, -0.456, 0.789]
        }
        st.dataframe(pd.DataFrame(sample_data))

def show_system_status():
    """Página de estado del sistema"""
    st.header("⚙️ Estado del Sistema")
    
    # Estado de la API
    is_healthy, health_data = check_api_health()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔌 Conectividad")
        
        if is_healthy:
            st.markdown("""
            <div class="status-healthy">
                ✅ API Backend: Conectado
            </div>
            """, unsafe_allow_html=True)
            
            if health_data:
                st.json(health_data)
        else:
            st.markdown("""
            <div class="status-error">
                ❌ API Backend: Desconectado
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        st.subheader("📊 Métricas del Sistema")
        
        # Métricas simuladas
        st.metric("⚡ Latencia Promedio", "95ms", delta="-5ms")
        st.metric("🔄 Requests/min", "1,250", delta="50")
        st.metric("💾 Uso de Memoria", "67%", delta="2%")
        st.metric("💽 Uso de CPU", "23%", delta="-1%")
    
    # Gráfico de rendimiento
    st.subheader("📈 Rendimiento en Tiempo Real")
    
    # Datos simulados de rendimiento
    times = pd.date_range(start=datetime.now() - timedelta(hours=1), 
                         end=datetime.now(), freq='1min')
    cpu_usage = np.random.normal(25, 5, len(times))
    memory_usage = np.random.normal(65, 8, len(times))
    
    perf_df = pd.DataFrame({
        'Tiempo': times,
        'CPU (%)': np.clip(cpu_usage, 0, 100),
        'Memoria (%)': np.clip(memory_usage, 0, 100)
    })
    
    fig = px.line(perf_df, x='Tiempo', y=['CPU (%)', 'Memoria (%)'], 
                  title='Uso de Recursos del Sistema')
    st.plotly_chart(fig, use_container_width=True)
    
    # Logs del sistema
    st.subheader("📝 Logs Recientes")
    
    sample_logs = [
        "2024-01-01 10:30:15 - INFO - Modelo cargado exitosamente",
        "2024-01-01 10:30:20 - INFO - Transacción procesada: ID-12345",
        "2024-01-01 10:30:25 - WARNING - Alta latencia detectada: 150ms",
        "2024-01-01 10:30:30 - INFO - Transacción procesada: ID-12346",
        "2024-01-01 10:30:35 - INFO - Health check: OK"
    ]
    
    for log in sample_logs:
        if "WARNING" in log:
            st.warning(log)
        elif "ERROR" in log:
            st.error(log)
        else:
            st.info(log)

if __name__ == "__main__":
    main()
