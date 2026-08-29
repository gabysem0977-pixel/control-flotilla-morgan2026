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
st.markdown("Vista general consolidada con evaluación de rangos de St. Miles (Columna Q).")
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

# Omitimos la última fila si contiene el total general de la hoja original de Excel
if len(df_raw) > 0:
    df_raw = df_raw.iloc[:-1].copy()

# Manejo seguro de fechas (Columna J / índice 9)
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

# Columna St. Miles: Tomamos exactamente la columna Q (índice 16) o buscamos por nombre
if len(df_raw.columns) > 16:
    col_st_miles = df_raw.columns[16]
    df_raw["St.Miles"] = pd.to_numeric(df_raw[col_st_miles], errors="coerce").fillna(0)
elif "St. Miles" in df_raw.columns:
    df_raw["St.Miles"] = pd.to_numeric(df_raw["St. Miles"], errors="coerce").fillna(0)
else:
    mile_cols = [c for c in df_raw.columns if "mile" in c.lower()]
    df_raw["St.Miles"] = pd.to_numeric(df_raw[mile_cols[0]], errors="coerce").fillna(0) if mile_cols else 0

# Totales (Tarifa)
total_col = "Total" if "Total" in df_raw.columns else df_raw.columns[4] if len(df_raw.columns) > 4 else None
if total_col and total_col in df_raw.columns:
    df_raw["Total"] = pd.to_numeric(df_raw[total_col], errors="coerce").fillna(0)
else:
    df_raw["Total"] = 0

# Unidad basada en la Columna B (Settl.#, índice 1)
if len(df_raw.columns) > 1:
    col_settle = df_raw.columns[1]
    df_raw["Unidad"] = df_raw[col_settle].astype(str)
elif "Settl.#" in df_raw.columns:
    df_raw["Unidad"] = df_raw["Settl.#"].astype(str)
else:
    df_raw["Unidad"] = "Eco-General"

if "Created By" in df_raw.columns:
    df_raw["Operador"] = df_raw["Created By"]
elif "Operador" not in df_raw.columns:
    df_raw["Operador"] = "Sin Asignar"

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

unidades_sel = st.sidebar.multiselect("Unidad", options=df_raw["Unidad"].unique(), default=df_raw["Unidad"].unique())
operadores_sel = st.sidebar.multiselect("Operador / Creador", options=df_raw["Operador"].unique(), default=df_raw["Operador"].unique())

df_filtered = df_raw[
    (df_raw["Unidad"].isin(unidades_sel)) & 
    (df_raw["Operador"].isin(operadores_sel))
]

# ==========================================
# 4. LÓGICA SEGÚN EL MODO SELECCIONADO
# ==========================================

if modo_analisis == "General (Gerencia / Dirección)":
    
    # Preparamos los datos agrupados por Unidad y su categoría Target exacta
    df_unidades = df_filtered.groupby("Unidad")["St.Miles"].sum().reset_index()
    df_unidades.columns = ["Unidad", "Millas"]
    
    def clasificar_target(millas):
        if millas > 3000:
            return "UNIDADES 3,000 + MILLAS"
        elif millas > 2500:
            return "UNIDADES 2,500 - 3,000 MILLAS"
        elif millas > 2000:
            return "UNIDADES 2,000-2,500 MILLAS"
        elif millas > 1500:
            return "UNIDADES 1,500 - 2,000 MILLAS"
        else:
            return "UNIDADES BAJO 1,500 MILLAS"

    df_unidades["Rango Target"] = df_unidades["Millas"].apply(clasificar_target)
    
    conteo_targets = df_unidades["Rango Target"].value_counts().reset_index()
    conteo_targets.columns = ["Categoría Target", "Cantidad de Unidades"]
    
    categorias_orden = [
        "UNIDADES 3,000 + MILLAS",
        "UNIDADES 2,500 - 3,000 MILLAS",
        "UNIDADES 2,000-2,500 MILLAS",
        "UNIDADES 1,500 - 2,000 MILLAS",
        "UNIDADES BAJO 1,500 MILLAS"
    ]
    
    df_target_table = pd.DataFrame({"Categoría Target": categorias_orden})
    df_target_table = df_target_table.merge(conteo_targets, on="Categoría Target", how="left").fillna(0)
    df_target_table["Cantidad de Unidades"] = df_target_table["Cantidad de Unidades"].astype(int)
    
    total_unidades = df_target_table["Cantidad de Unidades"].sum()
    fila_total = pd.DataFrame({"Categoría Target": ["TOTAL"], "Cantidad de Unidades": [total_unidades]})
    df_target_table = pd.concat([df_target_table, fila_total], ignore_index=True)

    # 4 KPIs Superiores
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("1. Tarifa Promedio", f"${df_filtered['Total'].mean():,.2f}")
    col2.metric("2. Viajes Totales", f"{len(df_filtered):,}")
    col3.metric("3. Flotilla Activa", f"{df_filtered['Unidad'].nunique()} unidades")
    col4.metric("4. Total St. Miles", f"{df_filtered['St.Miles'].sum():,.1f} mi")
    
    st.markdown("---")
    
    # Sección dedicada al Target de Unidades Millas (Tabla + Gráfico)
    st.subheader("🎯 Target de Unidades Millas (Evaluación por Categoría)")
    
    tc1, tc2 = st.columns([1, 1.5])
    
    with tc1:
        st.markdown("**Tabla de Unidades por Rango**")
        st.dataframe(df_target_table.set_index("Categoría Target"), use_container_width=True)
        
    with tc2:
        st.markdown("**Gráfica de Distribución por Criterio Target**")
        fig_target = px.bar(
            df_target_table[df_target_table["Categoría Target"] != "TOTAL"],
            x="Categoría Target",
            y="Cantidad de Unidades",
            text="Cantidad de Unidades",
            color="Categoría Target",
            color_discrete_sequence=px.colors.sequential.Blues_r
        )
        fig_target.update_layout(xaxis_title="", yaxis_title="No. de Unidades", showlegend=False)
        st.plotly_chart(fig_target, use_container_width=True)

    st.markdown("---")
    
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("1. 🛣️ Detalle de Millas por Unidad (Columna Q - St. Miles)")
        fig_u = px.bar(df_unidades, x="Unidad", y="Millas", text_auto='.2s', color="Millas", color_continuous_scale="Blues")
        fig_u.add_hline(y=OBJETIVO_MILLAS_SEMANAL, line_dash="dash", line_color="red", annotation_text=f"Meta: {OBJETIVO_MILLAS_SEMANAL} mi", annotation_position="bottom right")
        st.plotly_chart(fig_u, use_container_width=True)
        
        st.subheader("3. 💰 Ingresos por Tarifa (Distribución)")
        fig_t = px.box(df_filtered, x="Destino", y="Total", color="Destino")
        fig_t.update_layout(yaxis_title="Tarifa Total ($)")
        st.plotly_chart(fig_t, use_container_width=True)

    with c2:
        st.subheader("2. 📍 Rendimiento por Destino")
        df_destinos = df_filtered.groupby("Destino")["St.Miles"].sum().reset_index()
        fig_d = px.pie(df_destinos, names="Destino", values="St.Miles", hole=0.4)
        st.plotly_chart(fig_d, use_container_width=True)
        
        st.subheader("4. 👤 Rendimiento por Operador / Creador")
        df_ops = df_filtered.groupby("Operador")[["St.Miles", "Total"]].mean().reset_index()
        fig_o = px.bar(df_ops, x="Operador", y="St.Miles", color="Total", text_auto='.2s', color_continuous_scale="Viridis")
        fig_o.update_layout(yaxis_title="Promedio de St. Miles")
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
        
        millas_act = df_actual["St.Miles"].sum()
        millas_ant = df_anterior["St.Miles"].sum()
        delta_millas = ((millas_act - millas_ant) / (millas_ant if millas_ant > 0 else 1)) * 100
        
        tarifa_act = df_actual["Total"].mean()
        tarifa_ant = df_anterior["Total"].mean()
        delta_tarifa = ((tarifa_act - tarifa_ant) / (tarifa_ant if tarifa_ant > 0 else 1)) * 100
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Millas St. (Semana Actual)", f"{millas_act:,.1f} mi", f"{delta_millas:+.1f}% vs semana ant.")
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
        
        total_millas_periodo = df_periodo['St.Miles'].sum()
        st.metric("Total de St. Miles en el Periodo Seleccionado", f"{total_millas_periodo:,.1f} mi")
        
        st.markdown("### 🎯 Desglose de Cumplimiento por Unidad en el Periodo")
        df_resumen_periodo = df_periodo.groupby("Unidad")["St.Miles"].sum().reset_index()
        df_resumen_periodo.columns = ["Unidad", "Millas Acumuladas"]
        
        def clasificar_target(millas):
            if millas > 3000:
                return "UNIDADES 3,000 + MILLAS"
            elif millas > 2500:
                return "UNIDADES 2,500 - 3,000 MILLAS"
            elif millas > 2000:
                return "UNIDADES 2,000-2,500 MILLAS"
            elif millas > 1500:
                return "UNIDADES 1,500 - 2,000 MILLAS"
            else:
                return "UNIDADES BAJO 1,500 MILLAS"

        df_resumen_periodo["Rango Target"] = df_resumen_periodo["Millas Acumuladas"].apply(clasificar_target)
        st.dataframe(df_resumen_periodo.style.format({"Millas Acumuladas": "{:,.1f}"}), use_container_width=True)

        st.markdown("---")
        df_tiempo = df_periodo.groupby("Dia")[["St.Miles"]].sum().reset_index()
        fig_tiempo = px.line(df_tiempo, x="Dia", y="St.Miles", markers=True, title="Evolución de St. Miles por Día en el Periodo")
        fig_tiempo.update_layout(yaxis_title="Millas Totales")
        st.plotly_chart(fig_tiempo, use_container_width=True)
    else:
        st.warning("No se encontraron rangos de fecha válidos en los reportes.")

# ==========================================
# PIE DE PÁGINA
# ==========================================
st.markdown("---")
st.caption("Sistema de Control Privado - Morgan Express © 2026")
