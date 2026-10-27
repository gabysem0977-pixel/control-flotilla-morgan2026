import datetime
import json
import pandas as pd
import plotly.express as px
import streamlit as st
import google.generativeai as genai
from PIL import Image

# ==========================================
# 1. CONFIGURACIÓN DE LA PÁGINA
# ==========================================
st.set_page_config(
    page_title="Dashboard | Control Flotilla Morgan",
    page_icon="🚚",
    layout="wide",
)

st.title("🚚 Dashboard Ejecutivo - Control de Flotilla")
st.markdown("---")

# ==========================================
# 2. INICIALIZAR MEMORIA DE DATOS (SESSION STATE)
# ==========================================
# Aquí se almacenan los datos de la semana actual. Si subes una imagen nueva, estos valores cambian solos.
if "datos_oficiales" not in st.session_state:
    st.session_state.datos_oficiales = {
        "expo_actual": 53,
        "nb_actual": 0,
        "sb_actual": 81,
        "total_loads_actual": 134,
        "total_unidades_target": 51,
        "u_3000_plus": 19,
        "u_2500_3000": 14,
        "u_2000_2500": 12,
        "u_1500_2000": 3,
        "u_bajo_1500": 3,
        "comentarios": [
            "321 OPS TEAM NO SALIERON POR SITUACION FAMILIAR",
            "612 NO SALIO POR CUESTION DE TALLER"
        ]
    }

# ==========================================
# 3. BARRA LATERAL (CARGA DE ARCHIVOS E IMÁGENES)
# ==========================================
try:
    st.sidebar.image("assets/logo.png", use_container_width=True)
except Exception:
    pass

st.sidebar.header("🎛️ 1. Cargar Resumen (Imagen BSCF)")
img_file = st.sidebar.file_uploader("Sube la imagen de la tabla semanal", type=["png", "jpg", "jpeg"])

if img_file is not None:
    if st.sidebar.button("🤖 Extraer Datos con IA"):
        with st.spinner("La IA está leyendo la tabla..."):
            try:
                # Conectar con Google Gemini Vision
                genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                # Cargar la imagen
                img = Image.open(img_file)
                
                # Instrucción estricta para la IA
                prompt = """
                Analiza esta tabla de reporte logístico.
                Extrae los valores numéricos de las cargas (loads), del 'TARGET DE UNIDADES MILLAS' y los comentarios ('COMMENTS').
                Devuelve ÚNICAMENTE un objeto JSON puro con esta estructura exacta, sin texto adicional ni formato markdown:
                {
                  "expo_actual": numero,
                  "nb_actual": numero,
                  "sb_actual": numero,
                  "total_loads_actual": numero,
                  "total_unidades_target": numero,
                  "u_3000_plus": numero,
                  "u_2500_3000": numero,
                  "u_2000_2500": numero,
                  "u_1500_2000": numero,
                  "u_bajo_1500": numero,
                  "comentarios": ["comentario 1", "comentario 2"]
                }
                """
                response = model.generate_content([prompt, img])
                
                # Limpiar y guardar la respuesta de la IA
                raw_json = response.text.replace("```json", "").replace("```", "").strip()
                nuevos_datos = json.loads(raw_json)
                
                # Actualizar la memoria y refrescar
                st.session_state.datos_oficiales = nuevos_datos
                st.sidebar.success("¡Datos extraídos y actualizados exitosamente!")
            except Exception as e:
                st.sidebar.error("Error al analizar la imagen. Verifica que agregaste la API KEY en los Secrets.")
                st.sidebar.write(e)

st.sidebar.markdown("---")
st.sidebar.header("🗂️ 2. Cargar Excel Operativo")
uploaded_file = st.sidebar.file_uploader(
    "Sube el archivo Excel de viajes", type=["xlsx", "xls", "csv"]
)

# [Procesamiento del Excel omitido por brevedad, es idéntico a tu código anterior]
df_raw = pd.DataFrame()
if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith(".csv"):
            df_raw = pd.read_csv(uploaded_file)
        else:
            df_raw = pd.read_excel(uploaded_file, header=7)
    except Exception as e:
        pass

if not df_raw.empty:
    df_raw.columns = df_raw.columns.astype(str).str.strip()
    date_col = df_raw.columns[9] if len(df_raw.columns) >= 10 else "Pickup"
    if date_col in df_raw.columns:
        df_raw["Pickup"] = pd.to_datetime(df_raw[date_col], errors="coerce")
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
# 4. MENÚ DE NAVEGACIÓN
# ==========================================
st.sidebar.markdown("---")
modo_analisis = st.sidebar.radio(
    "Selecciona el tipo de vista:",
    [
        "General (Gerencia / Dirección)",
        "Semana Anterior vs. Actual (Comparativo)",
        "Generador de Resumen (Automático)",
    ],
)

# Extraemos las variables actualizadas desde la Memoria (Session State)
datos = st.session_state.datos_oficiales

expo_actual = datos["expo_actual"]
nb_actual = datos["nb_actual"]
sb_actual = datos["sb_actual"]
total_loads_actual = datos["total_loads_actual"]

total_unidades_target = datos["total_unidades_target"]
u_3000_plus = datos["u_3000_plus"]
u_2500_3000 = datos["u_2500_3000"]
u_2000_2500 = datos["u_2000_2500"]
u_1500_2000 = datos["u_1500_2000"]
u_bajo_1500 = datos["u_bajo_1500"]
comentarios = datos["comentarios"]

# ==========================================
# 5. LÓGICA DE VISTAS (DASHBOARD)
# ==========================================

if modo_analisis == "General (Gerencia / Dirección)":
    df_loads_resumen = pd.DataFrame({
        "Categoría Load": ["EXPO DE NLD", "NB DE LAREDO", "VIAJES DE SB"],
        "Total Loads": [expo_actual, nb_actual, sb_actual],
    })

    categorias_orden = [
        "UNIDADES 3,000 + MILLAS", "UNIDADES 2,500 - 3,000 MILLAS",
        "UNIDADES 2,000-2,500 MILLAS", "UNIDADES 1,500 - 2,000 MILLAS", "UNIDADES BAJO 1,500 MILLAS"
    ]

    df_target_table = pd.DataFrame({
        "Categoría Target": categorias_orden,
        "Cantidad de Unidades": [u_3000_plus, u_2500_3000, u_2000_2500, u_1500_2000, u_bajo_1500],
    })

    fila_total = pd.DataFrame({"Categoría Target": ["TOTAL"], "Cantidad de Unidades": [total_unidades_target]})
    df_target_table = pd.concat([df_target_table, fila_total], ignore_index=True)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("1. Estado Operativo", "Activo")
    col2.metric("2. Total Loads", f"{total_loads_actual}", f"EXPO: {expo_actual} | SB: {sb_actual}")
    col3.metric("3. Flotilla Activa Target", f"{total_unidades_target} unidades")
    col4.metric("4. Unidades > 3,000 Millas", f"{u_3000_plus} un.", "Pendiente de Meta")

    st.markdown("---")
    st.markdown("### Métricas Operativas (Semana Actual)")

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
    st.subheader("Target de Unidades Millas (Semana Actual)")

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
    for comentario in comentarios:
        st.info(f"- {comentario}")

elif modo_analisis == "Semana Anterior vs. Actual (Comparativo)":
    st.title("⏱ Análisis Comparativo: Semana Anterior vs. Semana Actual")
    st.warning("Los datos de la 'Semana Actual' provienen de la última imagen escaneada por la IA.")
    
    df_comparativa_2w = pd.DataFrame({
        "Categoría / Rango": [
            "EXPO DE NLD", "NB DE LAREDO", "VIAJES DE SB", "TOTAL LOADS",
            "UNIDADES 3,000 + MILLAS", "UNIDADES 2,500 - 3,000 MILLAS", "UNIDADES 2,000-2,500 MILLAS",
            "UNIDADES 1,500 - 2,000 MILLAS", "UNIDADES BAJO 1,500 MILLAS", "TOTAL UNIDADES TARGET",
        ],
        "Semana Anterior": [47, 0, 79, 126, 23, 12, 4, 6, 5, 50],  # Archivo 32919
        "Semana Actual": [
            expo_actual, nb_actual, sb_actual, total_loads_actual,
            u_3000_plus, u_2500_3000, u_2000_2500, u_1500_2000, u_bajo_1500, total_unidades_target,
        ],
    })

    df_comparativa_2w["Diferencia (Var)"] = df_comparativa_2w["Semana Actual"] - df_comparativa_2w["Semana Anterior"]
    
    st.dataframe(df_comparativa_2w.set_index("Categoría / Rango"), use_container_width=True)

elif modo_analisis == "Generador de Resumen (Automático)":
    st.title("📊 Generador de Resumen Automático (BSCF)")
    if uploaded_file is None:
        st.info("💡 Por favor, sube tu archivo Excel en la barra lateral izquierda para generar el resumen.")
    else:
        st.success("¡Archivo Excel procesado!")
        st.dataframe(df_raw.head(10), use_container_width=True)

st.markdown("---")
st.caption("Sistema de Control Privado - Morgan Express © 2026")
    
