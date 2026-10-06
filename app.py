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
st.markdown("Vista general consolidada: Operaciones, Comparativas y Cuentas por Cobrar.")
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
# 3. CONEXIÓN SEGURA A LA NUBE (GOOGLE SHEETS PARA OPERACIONES)
# ==========================================
conn = st.connection("gsheets", type=GSheetsConnection)
url_excel_agosto = "https://docs.google.com/spreadsheets/d/1d2iBvDFT03GvtsLtLOxkEMNK5xiEp06cY-yPG7m8ITE/edit?usp=sharing"

@st.cache_data(ttl=600)
def load_data(url):
    try:
        data = conn.read(spreadsheet=url, header=7)
        return data
    except Exception as e:
        return pd.DataFrame() # Retorna DF vacío si falla

with st.spinner("Descargando datos operativos desde la nube..."):
    df_raw = load_data(url_excel_agosto)

# Procesamiento de Google Sheets (Solo si se cargó correctamente)
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
    
    # Extraer Origen, Destino, Millas, Unidad, etc.
    if "Orig-Dest" in df_raw.columns:
        splitted = df_raw["Orig-Dest"].str.split(" - ", n=1, expand=True)
        df_raw["Origen"] = splitted[0].str.strip()
        df_raw["Destino"] = splitted[1].str.strip()
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

# NUEVO MENÚ CON LA PESTAÑA DE AR AGING
modo_analisis = st.sidebar.radio(
    "Selecciona el tipo de vista:",
    [
        "General (Gerencia / Dirección)",
        "Semana Anterior vs. Actual (Comparativo)",
        "Periodos Definidos (Google Sheets)",
        "Cuentas por Cobrar (AR Aging)"
    ],
)

# Filtros para la sección de Periodos (Google Sheets)
df_filtered = df_raw.copy()
if not df_raw.empty and modo_analisis == "Periodos Definidos (Google Sheets)":
    st.sidebar.markdown("---")
    st.sidebar.subheader("Filtros Operativos")
    unidades_sel = st.sidebar.multiselect("Unidad", options=df_raw["Unidad"].unique(), default=df_raw["Unidad"].unique())
    df_filtered = df_raw[df_raw["Unidad"].isin(unidades_sel)]

# ==========================================
# 5. LÓGICA SEGÚN EL MODO SELECCIONADO
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
    st.info("""
    - **342:** Op en descanso.
    """)

elif modo_analisis == "Semana Anterior vs. Actual (Comparativo)":
    st.title("⏱️ Análisis Comparativo: Semana Anterior vs. Semana Actual")
    st.markdown("Comparativa directa basada estrictamente en los reportes oficiales.")
    
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
            
            st.markdown("### 🎯 Desglose de Cumplimiento por Unidad en el Periodo")
            df_resumen_periodo = df_periodo.groupby("Unidad")["St.Miles"].sum().reset_index()
            df_resumen_periodo.columns = ["Unidad", "Millas Acumuladas"]
            
            def clasificar_target(millas):
                if millas > 3000: return "UNIDADES 3,000 + MILLAS"
                elif millas >= 2500: return "UNIDADES 2,500 - 3,000 MILLAS"
                elif millas >= 2000: return "UNIDADES 2,000-2,500 MILLAS"
                elif millas >= 1500: return "UNIDADES 1,500 - 2,000 MILLAS"
                else: return "UNIDADES BAJO 1,500 MILLAS"

            df_resumen_periodo["Rango Target"] = df_resumen_periodo["Millas Acumuladas"].apply(clasificar_target)
            st.dataframe(df_resumen_periodo.style.format({"Millas Acumuladas": "{:,.1f}"}), use_container_width=True)
        else:
            st.warning("No se encontraron fechas válidas en los registros de Google Sheets.")
    else:
        st.error("No se pudieron cargar los datos de la nube para este análisis.")

elif modo_analisis == "Cuentas por Cobrar (AR Aging)":
    st.title("💸 Dashboard de Cuentas por Cobrar (AR Aging)")
    st.markdown("Análisis estratégico de cartera, antigüedad de saldos y concentración de clientes.")
    
    # Widget en la barra lateral para subir archivo
    st.sidebar.markdown("---")
    st.sidebar.info("Sube tu archivo Excel de Cuentas por Cobrar para visualizar los datos.")
    uploaded_file = st.sidebar.file_uploader("Actualizar reporte AR Aging", type=["xlsx", "xls", "csv"])
    
    # Nombre del archivo local esperado (por si ya lo tienes en la carpeta)
    archivo_ar = "Morgan_Ports_AR_Aging_14-Sep-2026_Presentado (1).xlsx"
    
    df_ar = pd.DataFrame()
    
    try:
        if uploaded_file is not None:
            if uploaded_file.name.endswith('.csv'):
                df_ar = pd.read_csv(uploaded_file)
            else:
                df_ar = pd.read_excel(uploaded_file)
            st.success("¡Datos de Cuentas por Cobrar cargados exitosamente desde el archivo subido!")
        else:
            # Intenta cargar el archivo si está en la misma carpeta del script
            df_ar = pd.read_excel(archivo_ar)
            st.success(f"¡Datos cargados exitosamente desde {archivo_ar}!")
    except FileNotFoundError:
        st.warning("⚠️ Sube tu reporte AR Aging usando el botón de la barra lateral izquierda para generar los indicadores.")
    except Exception as e:
        st.error(f"Ocurrió un error al procesar el archivo: {e}")
        
    if not df_ar.empty:
        # Detección inteligente de columnas
        col_cliente = df_ar.columns[0] 
        for c in df_ar.columns:
            if any(palabra in str(c).lower() for palabra in ["cliente", "customer", "name", "nombre", "port"]):
                col_cliente = c
                break
                
        col_total = df_ar.columns[-1] 
        for c in df_ar.columns:
            if any(palabra in str(c).lower() for palabra in ["total", "balance", "monto", "saldo", "due", "usd"]):
                col_total = c
                break
                
        df_ar[col_total] = pd.to_numeric(df_ar[col_total], errors="coerce").fillna(0)
        
        # Cálculos Financieros
        cartera_total = df_ar[col_total].sum()
        total_clientes = df_ar[col_cliente].nunique()
        promedio_deuda = cartera_total / total_clientes if total_clientes > 0 else 0
        
        st.markdown("### 📊 Indicadores Clave de Desempeño (KPIs)")
        c1, c2, c3 = st.columns(3)
        c1.metric("1. Cartera Total Vigente", f"${cartera_total:,.2f}")
        c2.metric("2. Clientes con Saldo Pendiente", f"{total_clientes}")
        c3.metric("3. Promedio de Deuda por Cliente", f"${promedio_deuda:,.2f}")
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🏆 Top 10 Clientes Deudores")
            df_top10 = df_ar.groupby(col_cliente)[col_total].sum().reset_index().sort_values(by=col_total, ascending=False).head(10)
            
            fig_top = px.bar(
                df_top10, x=col_total, y=col_cliente, orientation='h', text=col_total,
                color=col_total, color_continuous_scale="Reds"
            )
            fig_top.update_traces(texttemplate='$%{text:,.0f}', textposition='outside')
            fig_top.update_layout(yaxis={'categoryorder':'total ascending'}, xaxis_title="Deuda Total ($)", yaxis_title="Cliente")
            st.plotly_chart(fig_top, use_container_width=True)
            
        with col2:
            st.subheader("📅 Distribución por Antigüedad (Aging)")
            aging_cols = [c for c in df_ar.columns if any(x in str(c).lower() for x in ['current', 'corriente', '1-30', '31-60', '61-90', '>90', '90+', 'over'])]
            
            if aging_cols:
                for c in aging_cols:
                    df_ar[c] = pd.to_numeric(df_ar[c], errors="coerce").fillna(0)
                aging_sums = df_ar[aging_cols].sum().reset_index()
                aging_sums.columns = ['Antigüedad', 'Monto']
                
                fig_aging = px.pie(
                    aging_sums, names='Antigüedad', values='Monto', hole=0.4, 
                    color_discrete_sequence=px.colors.sequential.OrRd
                )
                fig_aging.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_aging, use_container_width=True)
            else:
                st.info("💡 La gráfica de pastel no está disponible porque el Excel subido no tiene las columnas clásicas de rangos de días (Current, 1-30, etc.).")
        
        st.markdown("---")
        st.subheader("📋 Detalle Completo del Reporte AR Aging")
        st.dataframe(df_ar, use_container_width=True)

# ==========================================
# PIE DE PÁGINA
# ==========================================
st.markdown("---")
st.caption("Sistema de Control Privado - Morgan Express © 2026")
