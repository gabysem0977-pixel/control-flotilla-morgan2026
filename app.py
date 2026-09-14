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
st.markdown("Vista general consolidada con comparativa semanal de métricas operativas y target de unidades.")
st.markdown("---")

# ==========================================
# 1. CONEXIÓN SEGURA A LA NUBE (GOOGLE SHEETS)
# ==========================================
conn = st.connection("gsheets", type=GSheetsConnection)
url_excel_agosto = "https://docs.google.com/spreadsheets/d/1d2iBvDFT03GvtsLtLOxkEMNK5xiEp06cY-yPG7m8ITE/edit?usp=sharing"

@st.cache_data(ttl=600)
def load_data(url):
    try:
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

if len(df_raw) > 0:
    df_raw = df_raw.iloc[:-1].copy()

date_col = df_raw.columns[9] if len(df_raw.columns) >= 10 else "Pickup"
if date_col in df_raw.columns:
    df_raw[date_col] = pd.to_datetime(df_raw[date_col], errors="coerce")
    df_raw["Pickup"] = df_raw[date_col]
else:
    df_raw["Pickup"] = pd.NaT

df_raw["Dia"] = df_raw["Pickup"].dt.date
df_raw["Anio"] = df_raw["Pickup"].dt.isocalendar().year
df_raw["SemanaNum"] = df_raw["Pickup"].dt.isocalendar().week
df_raw["MesNum"] = df_raw["Pickup"].dt.month

if "Orig-Dest" in df_raw.columns:
    splitted = df_raw["Orig-Dest"].str.split(" - ", n=1, expand=True)
    df_raw["Origen"] = splitted[0].str.strip()
    df_raw["Destino"] = splitted[1].str.strip()
elif "Destino" not in df_raw.columns:
    df_raw["Destino"] = "Desconocido"

if len(df_raw.columns) > 16:
    col_st_miles = df_raw.columns[16]
    df_raw["St.Miles"] = pd.to_numeric(df_raw[col_st_miles], errors="coerce").fillna(0)
elif "St. Miles" in df_raw.columns:
    df_raw["St.Miles"] = pd.to_numeric(df_raw["St. Miles"], errors="coerce").fillna(0)
else:
    mile_cols = [c for c in df_raw.columns if "mile" in c.lower()]
    df_raw["St.Miles"] = pd.to_numeric(df_raw[mile_cols[0]], errors="coerce").fillna(0) if mile_cols else 0

total_col = "Total" if "Total" in df_raw.columns else df_raw.columns[4] if len(df_raw.columns) > 4 else None
if total_col and total_col in df_raw.columns:
    df_raw["Total"] = pd.to_numeric(df_raw[total_col], errors="coerce").fillna(0)
else:
    df_raw["Total"] = 0

if len(df_raw.columns) > 1:
    col_settle = df_raw.columns[1]
    df_raw["Unidad"] = df_raw[col_settle].fillna("Vacía").astype(str).str.strip()
    df_raw.loc[(df_raw["Unidad"] == "") | (df_raw["Unidad"].str.lower() == "nan"), "Unidad"] = "Vacía"
elif "Settl.#" in df_raw.columns:
    df_raw["Unidad"] = df_raw["Settl.#"].fillna("Vacía").astype(str).str.strip()
    df_raw.loc[(df_raw["Unidad"] == "") | (df_raw["Unidad"].str.lower() == "nan"), "Unidad"] = "Vacía"
else:
    df_raw["Unidad"] = "Vacía"

if "Created By" in df_raw.columns:
    df_raw["Operador"] = df_raw["Created By"]
elif "Operador" not in df_raw.columns:
    df_raw["Operador"] = "Sin Asignar"
    
