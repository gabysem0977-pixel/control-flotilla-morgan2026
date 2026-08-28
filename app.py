import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import datetime

# ==========================================
# CONFIGURACIÓN DE LA PÁGINA
# ==========================================
st.set_page_config(
    page_title="Dashboard | Control Flotilla Morgan",
    page_icon="🚚",
    layout="wide"
)

st.title("🚚 Control de Flotilla - Morgan")
st.markdown("---")

# ==========================================
# CONEXIÓN SEGURA A LA NUBE (GOOGLE SHEETS)
# ==========================================
conn = st.connection("gsheets", type=GSheetsConnection)
url_excel_agosto = "https://docs.google.com/spreadsheets/d/1d2iBvDFT03GvtsLtLOxkEMNK5xiEp06cY-yPG7m8ITE/edit?usp=sharing" 

@st.cache_data(ttl=600)
def load_data(url):
    try:
        data = conn.read(spreadsheet=url)
        return data
    except Exception as e:
        st.error(f"Error al conectar con la base de datos: {e}")
        return None

with st.spinner("Descargando datos desde la nube..."):
    df_agosto = load_data(url_excel_agosto)

if df_agosto is None:
    st.warning("⚠️ No se pudieron cargar los datos de agosto. Verifica los permisos de Lector en tu Google Sheet.")
    st.stop()

st.success("¡Datos descargados con éxito!")

# ==========================================
# PANEL LATERAL (SIDEBAR)
# ==========================================
# Logotipo
try:
    st.sidebar.image("assets/logo.png", use_container_width=True)
except Exception:
    pass # Evita un error en pantalla si la imagen no se encuentra en la ruta especificada

st.sidebar.header("Filtros y Análisis")

# Selector en el panel lateral en lugar de pestañas
tipo_analisis = st.sidebar.radio(
    "Selecciona la vista:",
    ["📊 Análisis General", "📅 Semana Actual vs Anterior", "🗓️ Periodos Definidos"]
)

st.sidebar.markdown("---")

# ==========================================
# PROCESAMIENTO BASE
# ==========================================
# Nombre de la columna que contiene las fechas en tu archivo de Excel
col_fecha = 'Nombre_Columna_Fecha' # <--- CAMBIA ESTO POR TU COLUMNA REAL

if col_fecha in df_agosto.columns:
    df_agosto[col_fecha] = pd.to_datetime(df_agosto[col_fecha], errors='coerce')

# ==========================================
# VISTAS DINÁMICAS (Según selección lateral)
# ==========================================
if tipo_analisis == "📊 Análisis General":
    st.header("Visión General de la Flotilla")
    col1, col2, col3 = st.columns(3)
    try:
        with col1:
            st.metric(label="Total de Viajes Registrados", value=len(df_agosto))
        with col2:
            st.metric(label="Total de Datos", value=df_agosto.shape[0])
        with col3:
            st.metric(label="Variables Analizadas", value=df_agosto.shape[1])
    except Exception:
        pass
    
    st.dataframe(df_agosto, use_container_width=True)

elif tipo_analisis == "📅 Semana Actual vs Anterior":
    st.header("Comparativa Semanal")
    st.info("Para que este filtro funcione, asegúrate de cambiar 'Nombre_Columna_Fecha' por el nombre real de tu columna en el Excel.")
    
    if col_fecha in df_agosto.columns:
        st.dataframe(df_agosto[[col_fecha]].head(), use_container_width=True)
    else:
        st.warning(f"No se encontró la columna '{col_fecha}'. Edita el código con el nombre correcto.")

elif tipo_analisis == "🗓️ Periodos Definidos":
    st.header("Filtro por Rango de Fechas")
    colA, colB = st.columns(2)
    
    with colA:
        fecha_inicio = st.date_input("Fecha de inicio", datetime.date(2026, 8, 1))
    with colB:
        fecha_fin = st.date_input("Fecha de fin", datetime.date(2026, 8, 31))
        
    if col_fecha in df_agosto.columns:
        mascara = (df_agosto[col_fecha].dt.date >= fecha_inicio) & (df_agosto[col_fecha].dt.date <= fecha_fin)
        df_filtrado = df_agosto.loc[mascara]
        
        st.write(f"Mostrando datos desde **{fecha_inicio}** hasta **{fecha_fin}**:")
        st.metric(label="Viajes en este periodo", value=len(df_filtrado))
        st.dataframe(df_filtrado, use_container_width=True)
    else:
        st.warning("Configura el nombre de la columna de fecha en el código para activar este filtro.")

# ==========================================
# PIE DE PÁGINA
# ==========================================
st.markdown("---")
st.caption("Sistema de Control Privado - Morgan © 2026")
