import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

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

# Enlace al documento en la nube de Agosto
url_excel_agosto = "https://docs.google.com/spreadsheets/d/1d2iBvDFT03GvtsLtLOxkEMNK5xiEp06cY-yPG7m8ITE/edit?usp=sharing" 

@st.cache_data(ttl=600)
def load_data(url):
    try:
        data = conn.read(spreadsheet=url)
        return data
    except Exception as e:
        st.error(f"Error al conectar con la base de datos: {e}")
        return None

# ==========================================
# LECTURA DE DATOS
# ==========================================
with st.spinner("Descargando datos desde la nube..."):
    df_agosto = load_data(url_excel_agosto)

if df_agosto is None:
    st.warning("⚠️ No se pudieron cargar los datos de agosto. Verifica los permisos de Lector en tu Google Sheet.")
    st.stop()

st.success("¡Datos descargados y conectados con éxito!")

# ==========================================
# SECCIÓN 1: REPORTE DE AGOSTO
# ==========================================
st.header("📊 Reporte Financiero (Agosto)")

col1, col2, col3 = st.columns(3)

try:
    total_viajes = len(df_agosto)
    
    with col1:
        st.metric(label="Total de Viajes", value=total_viajes)
    with col2:
        st.metric(label="Registros Totales", value=df_agosto.shape[0])
    with col3:
        st.metric(label="Columnas Analizadas", value=df_agosto.shape[1])
        
except KeyError:
    st.info("Ajusta los nombres de las columnas para ver métricas matemáticas.")

st.subheader("Vista de Datos (Agosto)")
st.dataframe(df_agosto, use_container_width=True)


# ==========================================
# PIE DE PÁGINA
# ==========================================
st.markdown("---")
st.caption("Sistema de Control Privado - Morgan © 2026")
