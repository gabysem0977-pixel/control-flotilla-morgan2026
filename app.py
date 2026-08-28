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
        # header=7 toma exactamente la fila 8 como los encabezados de la tabla
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
# PROCESAMIENTO BASE (Columna J y nombres de fila 8)
# ==========================================
df_agosto.columns = df_agosto.columns.astype(str).str.strip()

if len(df_agosto.columns) >= 10:
    col_fecha = df_agosto.columns[9]  # Columna J (índice 9)
    df_agosto[col_fecha] = pd.to_datetime(df_agosto[col_fecha], errors='coerce')
else:
    col_fecha = None

# ==========================================
# VISTAS DINÁMICAS, KPIS Y GRÁFICAS
# ==========================================
if tipo_analisis == "📊 Análisis General":
    st.header("Visión General de la Flotilla - KPIs y Gráficas")
    
    # 4 KPIs solicitados (incluyendo la meta de 3,000 millas objetivo)
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(label="1. Millas por unidad (Objetivo: 3,000)", value=df_agosto.shape[0], delta="Meta: 3,000 mi")
    with col2:
        st.metric(label="2. Por destino", value=df_agosto.shape[0])
    with col3:
        st.metric(label="3. Por tarifa", value=df_agosto.shape[0])
    with col4:
        st.metric(label="4. Por operador", value=df_agosto.shape[0])
    
    st.markdown("---")
    
    # Gráficas de Análisis General
    st.subheader("📈 Gráficas de Rendimiento (Considerando Objetivo de 3,000 Millas)")
    
    g1, g2 = st.columns(2)
    with g1:
        st.markdown("**Distribución por Registros**")
        if len(df_agosto.columns) > 1:
            st.bar_chart(df_agosto.iloc[:, 1].value_counts().head(10))
        else:
            st.info("Datos insuficientes para la gráfica.")
            
    with g2:
        st.markdown("**Evolución Temporal (Columna J)**")
        if col_fecha and col_fecha in df_agosto.columns:
            df_temp = df_agosto.dropna(subset=[col_fecha]).copy()
            df_temp['MesDia'] = df_temp[col_fecha].dt.strftime('%m-%d')
            st.line_chart(df_temp['MesDia'].value_counts().sort_index())
        else:
            st.info("Columna J no disponible para la evolución temporal.")

    st.markdown("---")
    st.subheader("Detalle de la Base de Datos")
    st.dataframe(df_agosto, use_container_width=True)

elif tipo_analisis == "📅 Semana Actual vs Anterior":
    st.header("Comparativa Semanal")
    
    if col_fecha and col_fecha in df_agosto.columns:
        st.write(f"Métrica basada en la columna J: **{col_fecha}**")
        st.dataframe(df_agosto[[col_fecha]].head(), use_container_width=True)
    else:
        st.warning("No se pudo identificar correctamente la columna J en el archivo.")

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
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric(label="Registros en este periodo", value=len(df_filtrado))
        with col2:
            st.metric(label="Porcentaje del total", value=f"{(len(df_filtrado) / len(df_agosto) * 100):.1f}%" if len(df_agosto) > 0 else "0%")
            
        st.dataframe(df_filtrado, use_container_width=True)
    else:
        st.warning("No se pudo identificar la columna J para aplicar el filtro.")

# ==========================================
# PIE DE PÁGINA
# ==========================================
st.markdown("---")
st.caption("Sistema de Control Privado - Morgan © 2026")
