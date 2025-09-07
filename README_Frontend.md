# 🛡️ Frontend Streamlit - Sistema de Detección de Fraude Santiago Prado Larrarte

## 🌟 Características

Hola profe este frontend de Streamlit proporciona una interfaz web para interactuar con la API de detección de fraude.

### 📱 Páginas Disponibles:

1. **🏠 Dashboard**: Vista general del sistema con métricas y gráficos
2. **🔍 Predicción Individual**: Analiza transacciones una por una
3. **📊 Análisis Masivo**: Procesa múltiples transacciones desde CSV
4. **⚙️ Estado del Sistema**: Monitoreo de salud y rendimiento

## 🚀 Cómo Usar

### Opción 1: Con Docker (Recomendado)

```bash
# Levantar toda la infraestructura incluyendo frontend
docker-compose up -d

# Acceder al frontend
http://localhost:8501
```

### Opción 2: Desarrollo Local

```bash
# Instalar dependencias
pip install streamlit plotly requests pandas numpy

# Ejecutar el frontend
streamlit run streamlit_app.py

# Acceder al frontend
http://localhost:8501
```

## 🎯 Uso de la Aplicación

### 1. Predicción Individual

1. Ve a la página "🔍 Predicción Individual"
2. Haz clic en "🎲 Generar Transacción de Ejemplo" para datos automáticos
3. O ingresa manualmente:
   - **Monto**: Valor de la transacción
   - **Tiempo**: Segundos desde medianoche (0-86399)
   - **V1-V28**: Características PCA de la transacción
4. Haz clic en "🚀 Analizar Transacción"

### 2. Análisis Masivo

1. Ve a la página "📊 Análisis Masivo"
2. Sube un archivo CSV con formato:
   ```csv
   time,amount,v1,v2,v3,...,v28
   43200,150.50,-1.234,0.876,...,0.123
   54000,2500.00,0.567,-1.234,...,-0.456
   ```
3. Haz clic en "🚀 Procesar Lote"

### 3. Monitoreo del Sistema

1. Ve a "⚙️ Estado del Sistema"
2. Verifica la conectividad con la API
3. Revisa métricas de rendimiento
4. Consulta logs recientes

## 🎨 Características Visuales

- **Diseño Responsive**: Se adapta a diferentes tamaños de pantalla
- **Tema Personalizado**: Colores coherentes con gradientes atractivos
- **Indicadores Visuales**: Cards de estado con colores intuitivos
- **Gráficos Interactivos**: Usando Plotly para visualizaciones dinámicas
- **Animaciones**: Spinners y transiciones suaves

## 🔧 Configuración

### Variables de Entorno

- `API_BASE_URL`: URL de la API backend (default: http://localhost:8000)
- `STREAMLIT_SERVER_PORT`: Puerto del servidor (default: 8501)

### Personalización

Puedes modificar el tema editando la sección CSS en `streamlit_app.py`:

```python
# Cambiar colores principales
primaryColor = "#667eea"  # Color principal
backgroundColor = "#FFFFFF"  # Fondo
secondaryBackgroundColor = "#f0f2f6"  # Fondo secundario
textColor = "#262730"  # Color del texto
```

## 🛠️ Solución de Problemas

### ❌ "API no está disponible"
- Verifica que el backend esté ejecutándose en el puerto 8000
- Comprueba la conectividad de red entre contenedores

### 🐌 "Tiempo de respuesta lento"
- Revisa los logs del backend para errores
- Verifica recursos del sistema (CPU/Memoria)

### 🔄 "Error de conexión"
- Asegúrate de que `API_BASE_URL` esté configurado correctamente
- Verifica que no haya firewalls bloqueando las conexiones

## 📝 Ejemplo de Transacción

```json
{
  "time": 43200,
  "amount": 150.50,
  "v1": -1.234,
  "v2": 0.876,
  "v3": 2.101,
  ...
  "v28": 0.123
}
```

## 🎯 Interpretación de Resultados

- **🟢 Transacción Segura**: Probabilidad de fraude < 50%
- **🔴 Transacción Sospechosa**: Probabilidad de fraude ≥ 50%
- **Modelos Disponibles**:
  - Regresión Logística
  - K-Vecinos Cercanos
  - Máquina de Vectores de Soporte (SVM)
  - Árbol de Decisión

## 🔗 URLs Importantes

- **Frontend**: http://localhost:8501
- **API Backend**: http://localhost:8000
- **Documentación API**: http://localhost:8000/docs
- **Kafka UI**: http://localhost:8080

¡Disfruta usando el sistema de detección de fraude! 🚀
