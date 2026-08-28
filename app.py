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
        # Usamos header=7 para que la fila 8 sea la cabecera de la tabla
        data = conn.read(spreadsheet=url, header=7)
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
try:
    st.sidebar.image("assets/logo.png", use_container_width=True)
except Exception:
    pass

st.sidebar.header("Filtros y Análisis")

tipo_analisis = st.sidebar.radio(
    "Selecciona la vista:",
    ["📊 Análisis General", "📅 Semana Actual vs Anterior", "🗓️ Periodos Definidos"]
)

st.sidebar.markdown("---")

# ==========================================
# PROCESAMIENTO BASE (Columna J)
# ==========================================
if len(df_agosto.columns) >= 10:
    col_fecha = df_agosto.columns[9]  # Columna J (índice 9)
    df_agosto[col_fecha] = pd.to_datetime(df_agosto[col_fecha], errors='coerce')
else:
    col_fecha = None

# ==========================================
# VISTAS DINÁMICAS Y KPIs
# ==========================================
if tipo_analisis == "📊 Análisis General":
    st.header("Visión General de la Flotilla")
    
    # KPIs solicitados
    col1, col2, col3, col4 = st.columns(4)
    try:
        with col1:
            st.metric(label="Total de Registros", value=df_agosto.shape[0])
        with col2:
            st.metric(label="Total de Columnas", value=df_agosto.shape[1])
        with col3:
            st.metric(label="Viajes / Filas", value=len(df_agosto))
        with col4:
            st.metric(label="Estado", value="Conectado")
    except Exception:
        pass
    
    st.markdown("---")
    st.subheader("Detalle de la Base de Datos")
    st.dataframe(df_agosto, use_container_width=True)

elif tipo_analisis == "📅 Semana Actual vs Anterior":
    st.header("Comparativa Semanal")
    
    if col_fecha and col_fecha in df_agosto.columns:
        st.write(f"Métrica basada en la columna J: **{col_fecha}**")
        st.dataframe(df_agosto[[col_fecha]].head(), use_container_width=True)
    else:
        st.warning("No se pudo identificar correctamente la columna J en el archivo para la comparativa semanal.")

elif tipo_analisis == "🗓️ Periodos Definidos":
    st.header("Filtro por Rango de Fechas")
    colA, colB = st.columns(2)
    
    with colA:
        fecha_inicio = st.date_input("Fecha de inicio", datetime.date(2026, 8, 1))
    with colB:
        fecha_fin = st.date_input("Fecha de fin", datetime.date(2026, 8, 31))
        
    if col_fecha and col_fecha in df_agosto.columns:
        mascara = (df_agosto[col_fecha].dt.date >= fecha_inicio) & (df_agosto[col_fecha].dt.date <= fecha_fin)
        df_filtrado = df_agosto.loc[mascara]
        
        st.write(f"Mostrando datos desde **{fecha_inicio}** hasta **{fecha_fin}**:")
        
        # KPIs específicos para el periodo filtrado
        col1, col2 = st.columns(2)
        with col1:
            st.metric(label="Registros en este periodo", value=len(df_filtrado))
        with col2:
            st.metric(label="Porcentaje del total", value=f"{(len(df_filtrado) / len(df_agosto) * 100):.1f}%" if len(df_agosto) > 0 else "0%")
            
        st.dataframe(df_filtrado, use_container_width=True)
    else:
        st.warning("No se pudo identificar la columna J para aplicar el filtro de fechas.")

# ==========================================
# PIE DE PÁGINA
# ==========================================
st.markdown("---")
st.caption("Sistema de Control Privado - Morgan © 2026")
