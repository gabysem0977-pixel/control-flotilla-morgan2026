import datetime
import pandas as pd
import plotly.express as px
import streamlit as st
from streamlit_gsheets import GSheetsConnection

# ==========================================
# 1. CONFIGURACIÓN DE LA PÁGINA
# ==========================================
st.set_page_config(
    page_title="Dashboard | Control Flotilla Morgan",
    page_icon="🚚",
    layout="wide",
)

# Constante de Negocio
OBJETIVO_MILLAS_SEMANAL = 3000

st.title("🚚 Dashboard Ejecutivo - Control de Flotilla")
st.markdown("Vista general consolidada: Operaciones, Comparativas y Resumen Automático (Google Sheets).")
st.markdown("---")

# ==========================================
# 2. DATOS OFICIALES DE LA SEMANA ACTUAL (HARDCODED - IMAGEN BSCF)
# ==========================================
total_loads_actual = 121
expo_actual = 45
nb_actual = 0
sb_actual = 76

total_unidades_target = 44
u_3000_plus = 21
u_2500_3000 = 14
u_2000_2500 = 6
u_1500_2000 = 3
u_bajo_1500 = 0

# ==========================================
# 3. CONEXIÓN SEGURA A LA NUBE (GOOGLE SHEETS PRINCIPAL)
# ==========================================
conn = st.connection("gsheets", type=GSheetsConnection)
url_excel_agosto = "https://docs.google.com/spreadsheets/d/1d2iBvDFT03GvtsLtLOxkEMNK5xiEp06cY-yPG7m8ITE/edit?usp=sharing"

@st.cache_data(ttl=600)
def load_data(url):
    try:
        data = conn.read(spreadsheet=url, header=7)
        return data
    except Exception as e:
        return pd.DataFrame() 

with st.spinner("Descargando datos operativos desde Google Drive..."):
    df_raw = load_data(url_excel_agosto)

# Procesamiento de Google Sheets
if not df_raw.empty:
    df_raw.columns = df_raw.columns.astype(str).str.strip()
    if len(df_raw) > 0:
        df_raw = df_raw.iloc[:-1].copy()

    date_col = df_raw.columns[9] if len(df_raw.columns) >= 10 else "Pickup"
    if date_col in df_raw.columns:
        df_raw[date_col] = pd.to_datetime(df_raw[date_col], errors="coerce")
        df_raw["Pickup"] = df_raw[date_col]
    else:
        df_raw["Pickup"] = pd.NaT

    df_raw["Dia"] = df_raw["Pickup"].dt.date
    
    if "Orig-Dest" in df_raw.columns:
        splitted = df_raw["Orig-Dest"].str.split(" - ", n=1, expand=True)
        if len(splitted.columns) == 2:
            df_raw["Origen"] = splitted[0].str.strip()
            df_raw["Destino"] = splitted[1].str.strip()
        else:
            df_raw["Destino"] = df_raw["Orig-Dest"]
    elif "Destino" not in df_raw.columns:
        df_raw["Destino"] = "Desconocido"

    if len(df_raw.columns) > 16:
        df_raw["St.Miles"] = pd.to_numeric(df_raw[df_raw.columns[16]], errors="coerce").fillna(0)
    else:
        df_raw["St.Miles"] = 0

    if len(df_raw.columns) > 1:
        df_raw["Unidad"] = df_raw[df_raw.columns[1]].fillna("Vacía").astype(str).str.strip()
    else:
        df_raw["Unidad"] = "Vacía"

# ==========================================
# 4. BARRA LATERAL (SIDEBAR Y MENÚ)
# ==========================================
try:
    st.sidebar.image("assets/logo.png", use_container_width=True)
except Exception:
    pass

st.sidebar.header("🎛️ Panel de Control")

modo_analisis = st.sidebar.radio(
    "Selecciona el tipo de vista:",
    [
        "General (Gerencia / Dirección)",
        "Semana Anterior vs. Actual (Comparativo)",
        "Periodos Definidos (Google Sheets)",
        "Generador de Resumen (Automático Google Sheets)"
    ],
)

df_filtered = df_raw.copy()
if not df_raw.empty and modo_analisis == "Periodos Definidos (Google Sheets)":
    st.sidebar.markdown("---")
    st.sidebar.subheader("Filtros Operativos")
    unidades_sel = st.sidebar.multiselect("Unidad", options=df_raw["Unidad"].unique(), default=df_raw["Unidad"].unique())
    df_filtered = df_raw[df_raw["Unidad"].isin(unidades_sel)]

# ==========================================
# 5. LÓGICA PRINCIPAL
# ==========================================

if modo_analisis == "General (Gerencia / Dirección)":
    
    df_loads_resumen = pd.DataFrame({
        "Categoría Load": ["EXPO DE NLD", "NB DE LAREDO", "VIAJES DE SB"],
        "Total Loads": [expo_actual, nb_actual, sb_actual]
    })

    categorias_orden = [
        "UNIDADES 3,000 + MILLAS", "UNIDADES 2,500 - 3,000 MILLAS",
        "UNIDADES 2,000-2,500 MILLAS", "UNIDADES 1,500 - 2,000 MILLAS",
        "UNIDADES BAJO 1,500 MILLAS"
    ]
    
    df_target_table = pd.DataFrame({
        "Categoría Target": categorias_orden,
        "Cantidad de Unidades": [u_3000_plus, u_2500_3000, u_2000_2500, u_1500_2000, u_bajo_1500]
    })
    
    fila_total = pd.DataFrame({"Categoría Target": ["TOTAL"], "Cantidad de Unidades": [total_unidades_target]})
    df_target_table = pd.concat([df_target_table, fila_total], ignore_index=True)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("1. Estado Operativo", "Activo")
    col2.metric("2. Total Loads", f"{total_loads_actual}", f"EXPO: {expo_actual} | SB: {sb_actual}")
    col3.metric("3. Flotilla Activa Target", f"{total_unidades_target} unidades")
    col4.metric("4. Unidades > 3,000 Millas", f"{u_3000_plus} un.", "Meta cumplida")
    
    st.markdown("---")
    st.markdown("### 📊 Métricas Operativas (Semana Actual)")
    
    lc1, lc2 = st.columns(2)
    with lc1:
        st.markdown("**Desglose de Loads**")
        st.dataframe(df_loads_resumen.set_index("Categoría Load"), use_container_width=True)
        
    with lc2:
        st.markdown("**Gráfica de Cargas por Tipo**")
        fig_loads = px.bar(
            df_loads_resumen, x="Categoría Load", y="Total Loads", text="Total Loads", 
            color="Categoría Load", color_discrete_sequence=px.colors.sequential.Teal_r
        )
        fig_loads.update_layout(xaxis_title="", yaxis_title="Loads", showlegend=False)
        st.plotly_chart(fig_loads, use_container_width=True)

    st.markdown("---")
    st.subheader("🎯 Target de Unidades Millas (Semana Actual)")
    
    tc1, tc2 = st.columns([1, 1.5])
    with tc1:
        st.markdown("**Tabla de Unidades por Rango**")
        st.dataframe(df_target_table.set_index("Categoría Target"), use_container_width=True)
        
    with tc2:
        st.markdown("**Gráfica de Distribución por Criterio Target**")
        fig_target = px.bar(
            df_target_table[df_target_table["Categoría Target"] != "TOTAL"],
            x="Categoría Target", y="Cantidad de Unidades", text="Cantidad de Unidades",
            color="Categoría Target", color_discrete_sequence=px.colors.sequential.Blues_r
        )
        fig_target.update_layout(xaxis_title="", yaxis_title="No. de Unidades", showlegend=False)
        st.plotly_chart(fig_target, use_container_width=True)

    st.markdown("---")
    st.subheader("📝 Comentarios y Observaciones de la Semana Actual")
    st.info("- **342:** Op en descanso.")

elif modo_analisis == "Semana Anterior vs. Actual (Comparativo)":
    st.title("⏱️ Análisis Comparativo: Semana Anterior vs. Semana Actual")
    
    df_comparativa_2w = pd.DataFrame({
        "Categoría / Rango": [
            "EXPO DE NLD", "NB DE LAREDO", "VIAJES DE SB", "TOTAL LOADS", 
            "UNIDADES 3,000 + MILLAS", "UNIDADES 2,500 - 3,000 MILLAS", 
            "UNIDADES 2,000-2,500 MILLAS", "UNIDADES 1,500 - 2,000 MILLAS", 
            "UNIDADES BAJO 1,500 MILLAS", "TOTAL UNIDADES TARGET"
        ],
        "Semana Anterior": [43, 0, 72, 115, 23, 15, 2, 1, 8, 49],
        "Semana Actual": [
            expo_actual, nb_actual, sb_actual, total_loads_actual,
            u_3000_plus, u_2500_3000, u_2000_2500, u_1500_2000, u_bajo_1500, total_unidades_target
        ]
    })
    
    df_comparativa_2w["Diferencia (Var)"] = df_comparativa_2w["Semana Actual"] - df_comparativa_2w["Semana Anterior"]
    
    # Calculo de variacion protegido
    var_relativa = df_comparativa_2w["Diferencia (Var)"] / df_comparativa_2w["Semana Anterior"].replace(0, 1)
    df_comparativa_2w["% Var"] = (var_relativa * 100).round(1).astype(str) + "%"

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Loads (Semana Actual)", f"{total_loads_actual} loads", "+6 vs sem. anterior")
    c2.metric("Unidades > 3,000 Millas", f"{u_3000_plus} unidades", "-2 vs sem. anterior")
    c3.metric("Total Unidades Evaluadas", f"{total_unidades_target} unidades", "-5 vs sem. anterior")

    st.markdown("---")
    st.subheader("📋 Tabla Comparativa Consolidada")
    st.dataframe(df_comparativa_2w.set_index("Categoría / Rango"), use_container_width=True)

    st.markdown("---")
    st.subheader("📊 Gráfica Comparativa de Rangos Target")
    df_melted_2w = df_comparativa_2w.iloc[4:9].melt(
        id_vars="Categoría / Rango", value_vars=["Semana Anterior", "Semana Actual"], 
        var_name="Semana", value_name="Unidades"
    )
    
    fig_comp_2w = px.bar(
        df_melted_2w, x="Categoría / Rango", y="Unidades", color="Semana", barmode="group",
        color_discrete_sequence=["#adb5bd", "#1864ab"]
    )
    fig_comp_2w.update_layout(xaxis_title="", yaxis_title="Cantidad de Unidades")
    st.plotly_chart(fig_comp_2w, use_container_width=True)

elif modo_analisis == "Periodos Definidos (Google Sheets)":
    st.title("📅 Análisis por Periodos Definidos y Seguimiento de Meta")
    if not df_filtered.empty and "Dia" in df_filtered.columns:
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
            
            st.markdown("### 🎯 Desglose
