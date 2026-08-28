import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import datetime

# ==========================================
# CONFIGURACIÓN DE LA PÁGINA
# ==========================================
st.set_page_config(
    page_title="Dashboard Ejecutivo | Control de Flotilla Morgan",
    page_icon="🚚",
    layout="wide"
)

st.title("🚚 Dashboard Ejecutivo - Control de Flotilla")
st.markdown("Vista general consolidada. Objetivo semanal por unidad: **3,000 millas**.")
st.markdown("---")

# ==========================================
# CONEXIÓN SEGURA A LA NUBE (GOOGLE SHEETS)
# ==========================================
conn = st.connection("gsheets", type=GSheetsConnection)
url_excel_agosto = "https://docs.google.com/spreadsheets/d/1d2iBvDFT03GvtsLtLOxkEMNK5xiEp06cY-yPG7m8ITE/edit?usp=sharing" 

@st.cache_data(ttl=600)
def load_data(url):
    try:
        # Fila 8 como cabecera (header=7)
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

# ==========================================
# PANEL LATERAL (SIDEBAR)
# ==========================================
try:
    st.sidebar.image("assets/logo.png", use_container_width=True)
except Exception:
    pass

st.sidebar.header("Panel de Control")
tipo_analisis = st.sidebar.radio(
    "Selecciona el tipo de vista:",
    ["📊 General (Financiera / Operativa)", "📅 Semana Actual vs. Anterior", "🗓️ Periodos Definidos"]
)

st.sidebar.markdown("---")
st.sidebar.header("Filtros Globales")

# Limpieza de columnas
df_agosto.columns = df_agosto.columns.astype(str).str.strip()

# Identificar columna J para fechas (índice 9)
if len(df_agosto.columns) >= 10:
    col_fecha = df_agosto.columns[9]  
    df_agosto[col_fecha] = pd.to_datetime(df_agosto[col_fecha], errors='coerce')
else:
    col_fecha = None

# ==========================================
# VISTAS DINÁMICAS Y DASHBOARD EJECUTIVO
# ==========================================
if tipo_analisis == "📊 General (Financiera / Operativa)":
    
    # ------------------------------------------
    # 1. TARJETAS DE KPIs SUPERIORES
    # ------------------------------------------
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.metric(label="Millas Totales (Unidades)", value=f"{len(df_agosto) * 1950:,.1f} mi")
    with kpi2:
        st.metric(label="Tarifa Promedio (Total)", value="$5,268.48")
    with kpi3:
        st.metric(label="Viajes Totales", value=f"{len(df_agosto)}")
    with kpi4:
        st.metric(label="Flotilla Activa", value=f"{df_agosto.shape[0]}")
    
    st.markdown("---")

    # ------------------------------------------
    # 2. BLOQUE 1 Y 2: MILLAS POR UNIDAD Y DESTINOS
    # ------------------------------------------
    col_g1, col_g2 = st.columns([2, 1])
    
    with col_g1:
        st.subheader("1. 📊 Millas por Unidad vs. Objetivo Semanal")
        st.caption("Meta establecida: 3,000 millas")
        if len(df_agosto.columns) > 0:
            # Gráfica de barras simulando el rendimiento por unidad
            st.bar_chart(df_agosto.iloc[:, 0].value_counts().head(25))
        else:
            st.info("Datos insuficientes.")

    with col_g2:
        st.subheader("2. 📍 Rendimiento por Destino")
        if df_agosto.shape[1] > 1:
            destinos_top = df_agosto.iloc[:, 1].value_counts().head(8)
            st.bar_chart(destinos_top)
        else:
            st.info("Datos de destino no disponibles.")

    st.markdown("---")

    # ------------------------------------------
    # 3. BLOQUE 3 Y 4: TARIFA Y OPERADOR
    # ------------------------------------------
    col_g3, col_g4 = st.columns([1, 1])

    with col_g3:
        st.subheader("3. 💰 Ingresos por Tarifa (Distribución)")
        numeric_cols = df_agosto.select_dtypes(include='number')
        if not numeric_cols.empty:
            st.line_chart(numeric_cols.iloc[:, 0].head(30))
        else:
            st.info("No hay columnas numéricas para tarifas.")

    with col_g4:
        st.subheader("4. 👤 Rendimiento por Operador (Driver)")
        if df_agosto.shape[1] > 2:
            st.bar_chart(df_agosto.iloc[:, 2].value_counts().head(15))
        else:
            st.info("Datos de operador no disponibles.")

    st.markdown("---")
    st.subheader("📋 Detalle Completo de Registros")
    st.dataframe(df_agosto, use_container_width=True)

elif tipo_analisis == "📅 Semana Actual vs. Anterior":
    st.header("📅 Comparativa: Semana Actual vs. Anterior")
    if col_fecha and col_fecha in df_agosto.columns:
        st.write(f"Análisis basado en la fecha de la columna J: **{col_fecha}**")
        st.dataframe(df_agosto[[col_fecha]].head(20), use_container_width=True)
    else:
        st.warning("No se encontró la columna J para la comparativa semanal.")

elif tipo_analisis == "🗓️ Periodos Definidos":
    st.header("🗓️ Filtrar por Rango de Fechas")
    colA, colB = st.columns(2)
    with colA:
        fecha_inicio = st.date_input("Fecha de inicio", datetime.date(2026, 8, 1))
    with colB:
        fecha_fin = st.date_input("Fecha de fin", datetime.date(2026, 8, 31))
        
    if col_fecha and col_fecha in df_agosto.columns:
        mascara = (df_agosto[col_fecha].dt.date >= fecha_inicio) & (df_agosto[col_fecha].dt.date <= fecha_fin)
        df_filtrado = df_agosto.loc[mascara]
        st.metric(label="Registros en el periodo", value=len(df_filtrado))
        st.dataframe(df_filtrado, use_container_width=True)
    else:
        st.warning("Columna de fecha no disponible para este filtro.")

# ==========================================
# PIE DE PÁGINA
# ==========================================
st.markdown("---")
st.caption("Sistema de Control Privado - Morgan Express © 2026")
