import datetime
import pandas as pd
import plotly.express as px
import streamlit as st

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
st.markdown("Vista general consolidada con los datos oficiales de la semana actual (BSCF).")
st.markdown("---")

# ==========================================
# DATOS OFICIALES DE LA SEMANA ACTUAL (IMAGEN BSCF)
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
# BARRA LATERAL (SIDEBAR Y LOGOTIPO)
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
    ],
)

# ==========================================
# LÓGICA SEGÚN EL MODO SELECCIONADO
# ==========================================

if modo_analisis == "General (Gerencia / Dirección)":
    
    df_loads_resumen = pd.DataFrame({
        "Categoría Load": ["EXPO DE NLD", "NB DE LAREDO", "VIAJES DE SB"],
        "Total Loads": [expo_actual, nb_actual, sb_actual]
    })

    categorias_orden = [
        "UNIDADES 3,000 + MILLAS",
        "UNIDADES 2,500 - 3,000 MILLAS",
        "UNIDADES 2,000-2,500 MILLAS",
        "UNIDADES 1,500 - 2,000 MILLAS",
        "UNIDADES BAJO 1,500 MILLAS"
    ]
    
    df_target_table = pd.DataFrame({
        "Categoría Target": categorias_orden,
        "Cantidad de Unidades": [u_3000_plus, u_2500_3000, u_2000_2500, u_1500_2000, u_bajo_1500]
    })
    
    fila_total = pd.DataFrame({"Categoría Target": ["TOTAL"], "Cantidad de Unidades": [total_unidades_target]})
    df_target_table = pd.concat([df_target_table, fila_total], ignore_index=True)

    # 4 KPIs Superiores basados en la tabla oficial
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
            df_loads_resumen,
            x="Categoría Load",
            y="Total Loads",
            text="Total Loads",
            color="Categoría Load",
            color_discrete_sequence=px.colors.sequential.Teal_r
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
            x="Categoría Target",
            y="Cantidad de Unidades",
            text="Cantidad de Unidades",
            color="Categoría Target",
            color_discrete_sequence=px.colors.sequential.Blues_r
        )
        fig_target.update_layout(xaxis_title="", yaxis_title="No. de Unidades", showlegend=False)
        st.plotly_chart(fig_target, use_container_width=True)

    st.markdown("---")
    st.subheader("📝 Comentarios y Observaciones de la Semana Actual")
    st.info("""
    - **342:** Op en descanso.
    """)

elif modo_analisis == "Semana Anterior vs. Actual (Comparativo)":
    st.title("⏱️ Análisis Comparativo: Semana Anterior vs. Semana Actual")
    st.markdown("Comparativa directa basada estrictamente en el reporte actual (BSCF).")
    
    df_comparativa_2w = pd.DataFrame({
        "Categoría / Rango": [
            "EXPO DE NLD", 
            "NB DE LAREDO", 
            "VIAJES DE SB", 
            "TOTAL LOADS", 
            "UNIDADES 3,000 + MILLAS", 
            "UNIDADES 2,500 - 3,000 MILLAS", 
            "UNIDADES 2,000-2,500 MILLAS", 
            "UNIDADES 1,500 - 2,000 MILLAS", 
            "UNIDADES BAJO 1,500 MILLAS",
            "TOTAL UNIDADES TARGET"
        ],
        "Semana Anterior": [43, 0, 72, 115, 23, 15, 2, 1, 8, 49],
        "Semana Actual": [
            expo_actual, nb_actual, sb_actual, total_loads_actual,
            u_3000_plus, u_2500_3000, u_2000_2500, u_1500_2000, u_bajo_1500, total_unidades_target
        ]
    })
    
    df_comparativa_2w["Diferencia (Var)"] = df_comparativa_2w["Semana Actual"] - df_comparativa_2w["Semana Anterior"]
    df_comparativa_2w["% Var"] = ((df_comparativa_2w["Diferencia (Var)"] / df_comparativa_2w["Semana Anterior"].replace(0, 1)) * 100).round(1).astype(str) + "%"

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Loads (Semana Actual)", f"{total_loads_actual} loads", "+6 vs sem. anterior")
    c2.metric("Unidades > 3,000 Millas", f"{u_3000_plus} unidades", "-2 vs sem. anterior")
    c3.metric("Total Unidades Evaluadas", f"{total_unidades_target} unidades", "-5 vs sem. anterior")

    st.markdown("---")
    st.subheader("📋 Tabla Comparativa Consolidada (Semana Anterior vs Actual)")
    st.dataframe(df_comparativa_2w.set_index("Categoría / Rango"), use_container_width=True)

    st.markdown("---")
    st.subheader("📊 Gráfica Comparativa de Rangos Target (Anterior vs Actual)")
    
    df_melted_2w = df_comparativa_2w.iloc[4:9].melt(
        id_vars="Categoría / Rango", 
        value_vars=["Semana Anterior", "Semana Actual"], 
        var_name="Semana", 
        value_name="Unidades"
    )
    
    fig_comp_2w = px.bar(
        df_melted_2w, 
        x="Categoría / Rango", 
        y="Unidades", 
        color="Semana", 
        barmode="group",
        color_discrete_sequence=["#adb5bd", "#1864ab"]
    )
    fig_comp_2w.update_layout(xaxis_title="", yaxis_title="Cantidad de Unidades")
    st.plotly_chart(fig_comp_2w, use_container_width=True)

    st.markdown("---")
    st.subheader("📝 Comentarios y Observaciones de la Semana Actual")
    st.info("""
    - **342:** Op en descanso.
    """)

# ==========================================
# PIE DE PÁGINA
# ==========================================
st.markdown("---")
st.caption("Sistema de Control Privado - Morgan Express © 2026")
