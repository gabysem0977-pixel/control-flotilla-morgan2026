import datetime
import pandas as pd
import plotly.express as px
import streamlit as st
from streamlit_gsheets import GSheetsConnection

# ==========================================
# CONFIGURACIÓN DE LA PÁGINA
# ==========================================
st.set_page_config(
    page_title="Dashboard | Control Flotilla Morgan",
    page_icon="🚚",
    layout="wide",
)

# Constante de Negocio
OBJETIVO_MILLAS_SEMANAL = 3000

st.title("🚚 Dashboard Ejecutivo - Control de Flotilla")
st.markdown(f"Vista general consolidada. **Objetivo semanal por unidad:** {OBJETIVO_MILLAS_SEMANAL:,.0f} millas.")
st.markdown("---")

# ==========================================
# 1. CONEXIÓN SEGURA A LA NUBE (GOOGLE SHEETS)
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
    df_raw = load_data(url_excel_agosto)

if df_raw is None or df_raw.empty:
    st.error("⚠️ No se pudieron cargar los datos de Google Sheets. Verifica los permisos de Lector en tu archivo.")
    st.stop()

# ==========================================
# 2. PROCESAMIENTO Y LIMPIEZA DE DATOS
# ==========================================
df_raw.columns = df_raw.columns.astype(str).str.strip()

# Manejo seguro de fechas (Columna J / índice 9 o columnas estándar)
date_col = df_raw.columns[9] if len(df_raw.columns) >= 10 else "Pickup"
if date_col in df_raw.columns:
    df_raw[date_col] = pd.to_datetime(df_raw[date_col], errors="coerce")
    df_raw["Pickup"] = df_raw[date_col]
else:
    df_raw["Pickup"] = pd.NaT

df_raw["Dia"] = df_raw["Pickup"].dt.date
df_raw["Anio"] = df_raw["Pickup"].dt.isocalendar().year
df_raw["SemanaNum"] = df_raw["Pickup"].dt.isocalendar().week

# Destinos
if "Orig-Dest" in df_raw.columns:
    splitted = df_raw["Orig-Dest"].str.split(" - ", n=1, expand=True)
    df_raw["Origen"] = splitted[0].str.strip()
    df_raw["Destino"] = splitted[1].str.strip()
elif "Destino" not in df_raw.columns:
    df_raw["Destino"] = "Desconocido"

# Millas y Totales (Asignación robusta)
miles_col = "L.Miles" if "L.Miles" in df_raw.columns else df_raw.columns[3] if len(df_raw.columns) > 3 else None
if miles_col and miles_col in df_raw.columns:
    df_raw["L.Miles"] = pd.to_numeric(df_raw[miles_col], errors="coerce").fillna(0)
else:
    df_raw["L.Miles"] = 0

total_col = "Total" if "Total" in df_raw.columns else df_raw.columns[4] if len(df_raw.columns) > 4 else None
if total_col and total_col in df_raw.columns:
    df_raw["Total"] = pd.to_numeric(df_raw[total_col], errors="coerce").fillna(0)
else:
    df_raw["Total"] = 0

# Operador y Unidad
if "Created By" in df_raw.columns:
    df_raw["Operador"] = df_raw["Created By"]
elif "Operador" not in df_raw.columns:
    df_raw["Operador"] = "Sin Asignar"

if "Load#" in df_raw.columns:
    df_raw["Unidad"] = "Eco-" + ((pd.to_numeric(df_raw["Load#"], errors="coerce").fillna(0) % 10) + 1).astype(str).str.zfill(3)
else:
    df_raw["Unidad"] = "Eco-001"

# ==========================================
# 3. BARRA LATERAL (SIDEBAR Y LOGOTIPO)
# ==========================================
try:
    st.sidebar.image("assets/logo.png", use_container_width=True)
except Exception:
    pass

st.sidebar.header("🎛️ Panel de Control")

modo_analisis = st.sidebar.radio(
    "Selecciona el tipo de vista:",
    ["General (Gerencia / Dirección)", "Semana Actual vs. Anterior", "Periodos Definidos"]
)

st.sidebar.markdown("---")
st.sidebar.subheader("Filtros Globales")

unidades_sel = st.sidebar.multiselect("Unidad (Eco)", options=df_raw["Unidad"].unique(), default=df_raw["Unidad"].unique())
operadores_sel = st.sidebar.multiselect("Operador / Creador", options=df_raw["Operador"].unique(), default=df_raw["Operador"].unique())

df_filtered = df_raw[
    (df_raw["Unidad"].isin(unidades_sel)) & 
    (df_raw["Operador"].isin(operadores_sel))
]

st.sidebar.markdown("---")
st.sidebar.info('💡 Archivo auxiliar disponible para referencia: "BSCF".')

# ==========================================
# 4. LÓGICA SEGÚN EL MODO SELECCIONADO
# ==========================================

if modo_analisis == "General (Gerencia / Dirección)":
    
    # 4 KPIs Principales en la parte superior
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("1. Millas Totales", f"{df_filtered['L.Miles'].sum():,.1f} mi", f"Meta: {OBJETIVO_MILLAS_SEMANAL} mi")
    col2.metric("2. Tarifa Promedio", f"${df_filtered['Total'].mean():,.2f}")
    col3.metric("3. Viajes Totales", f"{len(df_filtered):,}")
    col4.metric("4. Flotilla Activa", f"{df_filtered['Unidad'].nunique()} unidades")
    
    st.markdown("---")
    
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("1. 🛣️ Millas por Unidad vs. Objetivo Semanal")
        df_unidades = df_filtered.groupby("Unidad")["L.Miles"].sum().reset_index()
        df_unidades.columns = ["Unidad", "Millas"]
        
        df_unidades["Desviacion_Millas"] = df_unidades["Millas"] - OBJETIVO_MILLAS_SEMANAL
        df_unidades["Desviacion_Porc"] = (df_unidades["Desviacion_Millas"] / OBJETIVO_MILLAS_SEMANAL) * 100
        
        fig_u = px.bar(df_unidades, x="Unidad", y="Millas", text_auto='.2s', color="Millas", color_continuous_scale="Blues")
        fig_u.add_hline(y=OBJETIVO_MILLAS_SEMANAL, line_dash="dash", line_color="red", annotation_text=f"Meta: {OBJETIVO_MILLAS_SEMANAL} mi", annotation_position="bottom right")
        st.plotly_chart(fig_u, use_container_width=True)
        
        with st.expander("📋 Ver detalle de desviación por Unidad"):
            df_display = df_unidades.copy()
            df_display.columns = ["Unidad", "Millas Totales", "Dif. en Millas (vs Meta)", "% Desviación"]
            df_display["Millas Totales"] = df_display["Millas Totales"].round(1)
            df_display["Dif. en Millas (vs Meta)"] = df_display["Dif. en Millas (vs Meta)"].round(1)
            df_display["% Desviación"] = df_display["% Desviación"].round(1).astype(str) + "%"
            st.dataframe(df_display, use_container_width=True)
        
        st.subheader("3. 💰 Ingresos por Tarifa (Distribución)")
        fig_t = px.box(df_filtered, x="Destino", y="Total", color="Destino")
        fig_t.update_layout(yaxis_title="Tarifa Total ($)")
        st.plotly_chart(fig_t, use_container_width=True)

    with c2:
        st.subheader("2. 📍 Rendimiento por Destino")
        df_destinos = df_filtered.groupby("Destino")["L.Miles"].sum().reset_index()
        fig_d = px.pie(df_destinos, names="Destino", values="L.Miles", hole=0.4)
        st.plotly_chart(fig_d, use_container_width=True)
        
        st.subheader("4. 👤 Rendimiento por Operador / Creador")
        df_ops = df_filtered.groupby("Operador")[["L.Miles", "Total"]].mean().reset_index()
        fig_o = px.bar(df_ops, x="Operador", y="L.Miles", color="Total", text_auto='.2s', color_continuous_scale="Viridis")
        fig_o.update_layout(yaxis_title="Promedio de Millas")
        st.plotly_chart(fig_o, use_container_width=True)

    st.markdown("---")
    st.subheader("📋 Detalle Completo de Registros")
    st.dataframe(df_filtered, use_container_width=True)

elif modo_analisis == "Semana Actual vs. Anterior":
    st.title("⏱️ Análisis Comparativo: Semana Actual vs. Semana Anterior")
    
    semanas_unicas = sorted(df_filtered["SemanaNum"].dropna().unique())
    
    if len(semanas_unicas) >= 2:
        semana_actual = semanas_unicas[-1]
        semana_anterior = semanas_unicas[-2]
        
        st.info(f"Comparando la **Semana {semana_actual}** (Actual) contra la **Semana {semana_anterior}** (Anterior)")
        
        df_actual = df_filtered[df_filtered["SemanaNum"] == semana_actual]
        df_anterior = df_filtered[df_filtered["SemanaNum"] == semana_anterior]
        
        millas_act = df_actual["L.Miles"].sum()
        millas_ant = df_anterior["L.Miles"].sum()
        delta_millas = ((millas_act - millas_ant) / (millas_ant if millas_ant > 0 else 1)) * 100
        
        tarifa_act = df_actual["Total"].mean()
        tarifa_ant = df_anterior["Total"].mean()
        delta_tarifa = ((tarifa_act - tarifa_ant) / (tarifa_ant if tarifa_ant > 0 else 1)) * 100
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Millas (Semana Actual)", f"{millas_act:,.1f} mi", f"{delta_millas:+.1f}% vs semana ant.")
        c2.metric("Tarifa Promedio", f"${tarifa_act:,.2f}", f"{delta_tarifa:+.1f}% vs semana ant.")
        c3.metric("Cargas Registradas", f"{len(df_actual)}", f"{len(df_actual) - len(df_anterior)} vs semana ant.")

        st.markdown("---")
        st.subheader(f"Desglose de Cargas - Semana {semana_actual}")
        if not df_actual.empty:
            st.dataframe(df_actual, use_container_width=True)
        else:
            st.warning("No hay registros exactos para la semana actual seleccionada.")
    elif len(semanas_unicas) == 1:
        st.warning("Solo se detectó una semana de datos en los reportes cargados. Se necesitan al menos dos semanas para la comparativa.")
    else:
        st.warning("No hay semanas válidas en los reportes cargados.")

elif modo_analisis == "Periodos Definidos":
    st.title("📅 Análisis por Periodos Definidos y Seguimiento de Meta")
    
    valid_dates = df_filtered["Dia"].dropna()
    if not valid_dates.empty:
        min_date = valid_dates.min()
        max_date = valid_dates.max()
        
        col_f1, col_f2 = st.columns(2)
        f_inicio = col_f1.date_input("Fecha de Inicio", min_value=min_date, max_value=max_date, value=min_date)
        f_fin = col_f2.date_input("Fecha de Fin", min_value=min_date, max_value=max_date, value=max_date)
        
        df_periodo = df_filtered[(df_filtered["Dia"] >= f_inicio) & (df_filtered["Dia"] <= f_fin)]
        
        total_millas_periodo = df_periodo['L.Miles'].sum()
        st.metric("Total de Millas en el Periodo Seleccionado", f"{total_millas_periodo:,.1f} mi")
        
        st.markdown("### 🎯 Desglose de Cumplimiento por Unidad en el Periodo")
        df_resumen_periodo = df_periodo.groupby("Unidad")["L.Miles"].sum().reset_index()
        df_resumen_periodo["Desviacion_Millas"] = df_resumen_periodo["L.Miles"] - OBJETIVO_MILLAS_SEMANAL
        df_resumen_periodo["Desviacion_Porc"] = (df_resumen_periodo["Desviacion_Millas"] / OBJETIVO_MILLAS_SEMANAL) * 100
        
        df_resumen_periodo.columns = ["Unidad", "Millas Acumuladas", "Diferencia vs Meta (mi)", "% Desviación"]
        st.dataframe(df_resumen_periodo.style.format({
            "Millas Acumuladas": "{:,.1f}",
            "Diferencia vs Meta (mi)": "{:+,.1f}",
            "% Desviación": "{:+,.1f}%"
        }), use_container_width=True)

        st.markdown("---")
        df_tiempo = df_periodo.groupby("Dia")[["L.Miles"]].sum().reset_index()
        fig_tiempo = px.line(df_tiempo, x="Dia", y="L.Miles", markers=True, title="Evolución de Millas por Día en el Periodo")
        fig_tiempo.update_layout(yaxis_title="Millas Totales")
        st.plotly_chart(fig_tiempo, use_container_width=True)
    else:
        st.warning("No se encontraron rangos de fecha válidos en los reportes.")

# ==========================================
# PIE DE PÁGINA
# ==========================================
st.markdown("---")
st.caption("Sistema de Control Privado - Morgan Express © 2026")
