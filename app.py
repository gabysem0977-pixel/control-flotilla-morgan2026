import datetime
import pandas as pd
import plotly.express as px
import streamlit as st

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
st.markdown("Vista general consolidada con carga directa de archivos locales.")
st.markdown("---")

# ==========================================
# 2. DATOS OFICIALES DE LA SEMANA ACTUAL (BSCF)
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
# 3. CARGA DE ARCHIVO LOCAL (FILE UPLOADER)
# ==========================================
st.sidebar.header("🎛️ Panel de Control y Archivos")
uploaded_file = st.sidebar.file_uploader(
    "Sube tu archivo Excel operativo", type=["xlsx", "xls", "csv"]
)

df_raw = pd.DataFrame()

if uploaded_file is not None:
  try:
    if uploaded_file.name.endswith(".csv"):
      df_raw = pd.read_csv(uploaded_file)
    else:
      # Lee el archivo omitiendo las primeras 7 filas de encabezado institucional si aplica
      df_raw = pd.read_excel(uploaded_file, header=7)
    st.sidebar.success("¡Archivo cargado correctamente!")
  except Exception as e:
    st.sidebar.error(f"Error al leer el archivo: {e}")

# Procesamiento de los datos del archivo subido
if not df_raw.empty:
  df_raw.columns = df_raw.columns.astype(str).str.strip()
  if len(df_raw) > 0 and "Total" not in str(df_raw.iloc[-1].values):
    pass

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
    df_raw["St.Miles"] = pd.to_numeric(
        df_raw[df_raw.columns[16]], errors="coerce"
    ).fillna(0)
  else:
    df_raw["St.Miles"] = 0

  if len(df_raw.columns) > 1:
    df_raw["Unidad"] = (
        df_raw[df_raw.columns[1]].fillna("Vacía").astype(str).str.strip()
    )
  else:
    df_raw["Unidad"] = "Vacía"

# ==========================================
# 4. MENÚ DE NAVEGACIÓN (SIDEBAR)
# ==========================================
try:
  st.sidebar.image("assets/logo.png", use_container_width=True)
except Exception:
  pass

modo_analisis = st.sidebar.radio(
    "Selecciona el tipo de vista:",
    [
        "General (Gerencia / Dirección)",
        "Semana Anterior vs. Actual (Comparativo)",
        "Periodos Definidos",
        "Generador de Resumen (Automático)",
    ],
)

df_filtered = df_raw.copy()
if not df_raw.empty and modo_analisis == "Periodos Definidos":
  st.sidebar.markdown("---")
  st.sidebar.subheader("Filtros Operativos")
  opciones_unidades = df_raw["Unidad"].unique()
  unidades_sel = st.sidebar.multiselect(
      "Unidad", options=opciones_unidades, default=opciones_unidades
  )
  df_filtered = df_raw[df_raw["Unidad"].isin(unidades_sel)]

# ==========================================
# 5. LÓGICA PRINCIPAL DE VISTAS
# ==========================================

if modo_analisis == "General (Gerencia / Dirección)":
  df_loads_resumen = pd.DataFrame({
      "Categoría Load": ["EXPO DE NLD", "NB DE LAREDO", "VIAJES DE SB"],
      "Total Loads": [expo_actual, nb_actual, sb_actual],
  })

  categorias_orden = [
      "UNIDADES 3,000 + MILLAS",
      "UNIDADES 2,500 - 3,000 MILLAS",
      "UNIDADES 2,000-2,500 MILLAS",
      "UNIDADES 1,500 - 2,000 MILLAS",
      "UNIDADES BAJO 1,500 MILLAS",
  ]

  df_target_table = pd.DataFrame({
      "Categoría Target": categorias_orden,
      "Cantidad de Unidades": [
          u_3000_plus,
          u_2500_3000,
          u_2000_2500,
          u_1500_2000,
          u_bajo_1500,
      ],
  })

  fila_total = pd.DataFrame({
      "Categoría Target": ["TOTAL"],
      "Cantidad de Unidades": [total_unidades_target],
  })
  df_target_table = pd.concat([df_target_table, fila_total], ignore_index=True)

  col1, col2, col3, col4 = st.columns(4)
  col1.metric("1. Estado Operativo", "Activo")
  col2.metric(
      "2. Total Loads",
      f"{total_loads_actual}",
      f"EXPO: {expo_actual} | SB: {sb_actual}",
  )
  col3.metric("3. Flotilla Activa Target", f"{total_unidades_target} unidades")
  col4.metric(
      "4. Unidades > 3,000 Millas", f"{u_3000_plus} un.", "Meta cumplida"
  )

  st.markdown("---")
  st.markdown("### Métricas Operativas (Semana Actual)")

  lc1, lc2 = st.columns(2)
  with lc1:
    st.markdown("**Desglose de Loads**")
    st.dataframe(
        df_loads_resumen.set_index("Categoría Load"), use_container_width=True
    )

  with lc2:
    st.markdown("**Gráfica de Cargas por Tipo**")
    fig_loads = px.bar(
        df_loads_resumen,
        x="Categoría Load",
        y="Total Loads",
        text="Total Loads",
        color="Categoría Load",
        color_discrete_sequence=px.colors.sequential.Teal_r,
    )
    fig_loads.update_layout(
        xaxis_title="", yaxis_title="Loads", showlegend=False
    )
    st.plotly_chart(fig_loads, use_container_width=True)

  st.markdown("---")
  st.subheader("Target de Unidades Millas (Semana Actual)")

  tc1, tc2 = st.columns([1, 1.5])
  with tc1:
    st.markdown("**Tabla de Unidades por Rango**")
    st.dataframe(
        df_target_table.set_index("Categoría Target"), use_container_width=True
    )

  with tc2:
    st.markdown("**Gráfica de Distribución por Criterio Target**")
    fig_target = px.bar(
        df_target_table[df_target_table["Categoría Target"] != "TOTAL"],
        x="Categoría Target",
        y="Cantidad de Unidades",
        text="Cantidad de Unidades",
        color="Categoría Target",
        color_discrete_sequence=px.colors.sequential.Blues_r,
    )
    fig_target.update_layout(
        xaxis_title="", yaxis_title="No. de Unidades", showlegend=False
    )
    st.plotly_chart(fig_target, use_container_width=True)

elif modo_analisis == "Semana Anterior vs. Actual (Comparativo)":
  st.title("⏱ Análisis Comparativo: Semana Anterior vs. Semana Actual")

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
          "TOTAL UNIDADES TARGET",
      ],
      "Semana Anterior": [43, 0, 72, 115, 23, 15, 2, 1, 8, 49],
      "Semana Actual": [
          expo_actual,
          nb_actual,
          sb_actual,
          total_loads_actual,
          u_3000_plus,
          u_2500_3000,
          u_2000_2500,
          u_1500_2000,
          u_bajo_1500,
          total_unidades_target,
      ],
  })

  df_comparativa_2w["Diferencia (Var)"] = (
      df_comparativa_2w["Semana Actual"] - df_comparativa_2w["Semana Anterior"]
  )
  df_comparativa_2w["% Var"] = (
      (
          df_comparativa_2w["Diferencia (Var)"]
          / df_comparativa_2w["Semana Anterior"].replace(0, 1)
      )
      * 100
  ).round(1).astype(str) + "%"

  c1, c2, c3 = st.columns(3)
  c1.metric(
      "Total Loads (Semana Actual)",
      f"{total_loads_actual} loads",
      "+6 vs sem. anterior",
  )
  c2.metric(
      "Unidades > 3,000 Millas",
      f"{u_3000_plus} unidades",
      "-2 vs sem. anterior",
  )
  c3.metric(
      "Total Unidades Evaluadas",
      f"{total_unidades_target} unidades",
      "-5 vs sem. anterior",
  )

  st.markdown("---")
  st.subheader("📋 Tabla Comparativa Consolidada")
  st.dataframe(
      df_comparativa_2w.set_index("Categoría / Rango"), use_container_width=True
  )

elif modo_analisis == "Periodos Definidos":
  st.title("📅 Análisis por Periodos Definidos y Seguimiento de Meta")
  if uploaded_file is None:
    st.info(
        "💡 Por favor, sube tu archivo Excel en la barra lateral izquierda para"
        " habilitar el análisis."
    )
  elif not df_filtered.empty and "Dia" in df_filtered.columns:
    valid_dates = df_filtered["Dia"].dropna()
    if not valid_dates.empty:
      min_date = valid_dates.min()
      max_date = valid_dates.max()

      col_f1, col_f2 = st.columns(2)
      f_inicio = col_f1.date_input(
          "Fecha de Inicio", min_value=min_date, max_value=max_date, value=min_date
      )
      f_fin = col_f2.date_input(
          "Fecha de Fin", min_value=min_date, max_value=max_date, value=max_date
      )

      df_periodo = df_filtered[
          (df_filtered["Dia"] >= f_inicio) & (df_filtered["Dia"] <= f_fin)
      ]

      total_millas_periodo = df_periodo["St.Miles"].sum()
      st.metric(
          "Total de St. Miles en el Periodo Seleccionado",
          f"{total_millas_periodo:,.1f} mi",
      )

      st.markdown("### Desglose de Cumplimiento por Unidad")
      df_resumen_periodo = (
          df_periodo.groupby("Unidad")["St.Miles"].sum().reset_index()
      )
      df_resumen_periodo.columns = ["Unidad", "Millas Acumuladas"]

      def clasificar_target(millas):
        if millas > 3000:
          return "UNIDADES 3,000 + MILLAS"
        elif millas >= 2500:
          return "UNIDADES 2,500 - 3,000 MILLAS"
        elif millas >= 2000:
          return "UNIDADES 2,000-2,500 MILLAS"
        elif millas >= 1500:
          return "UNIDADES 1,500 - 2,000 MILLAS"
        else:
          return "UNIDADES BAJO 1,500 MILLAS"

      df_resumen_periodo["Rango Target"] = df_resumen_periodo[
          "Millas Acumuladas"
      ].apply(clasificar_target)
      st.dataframe(
          df_resumen_periodo.style.format({"Millas Acumuladas": "{:,.1f}"}),
          use_container_width=True,
      )
    else:
      st.warning("No se encontraron fechas válidas en el archivo.")
  else:
    st.error("Sube un archivo válido para consultar los periodos definidos.")

elif modo_analisis == "Generador de Resumen (Automático)":
  st.title("📊 Generador de Resumen Automático (BSCF)")
  if uploaded_file is None:
    st.info(
        "💡 Por favor, sube tu archivo Excel en la barra lateral izquierda para"
        " generar el resumen automático."
    )
  else:
    st.success("¡Archivo cargado y procesado exitosamente!")
    df_rep = df_raw.copy()
    if not df_rep.empty:
      col_millas = (
          "St. Miles"
          if "St. Miles" in df_rep.columns
          else (df_rep.columns[16] if len(df_rep.columns) > 16 else None)
      )
      df_rep["Millas_Calc"] = (
          pd.to_numeric(df_rep[col_millas], errors="coerce").fillna(0)
          if col_millas
          else 0
      )

      col_unidad = (
          "Settl.#"
          if "Settl.#" in df_rep.columns
          else (df_rep.columns[1] if len(df_rep.columns) > 1 else None)
      )
      df_rep["Unidad_Calc"] = (
          df_rep[col_unidad]
          .fillna("Vacía")
          .astype(str)
          .str.strip()
          if col_unidad
          else "Vacía"
      )
      df_rep = df_rep[df_rep["Unidad_Calc"].str.lower() != "nan"]

      if "Orig-Dest" in df_rep.columns:
        df_rep[["Origen", "Destino"]] = df_rep["Orig-Dest"].str.split(
            " - ", n=1, expand=True
        )
        df_rep["Destino"] = df_rep["Destino"].fillna("").astype(str)
      elif "Destino" not in df_rep.columns:
        df_rep["Destino"] = ""

      expo_loads = df_rep[
          df_rep["Destino"].str.contains("EXPO|NLD", case=False, na=False)
      ].shape[0]
      sb_loads = df_rep[
          df_rep["Destino"].str.contains("SB", case=False, na=False)
      ].shape[0]
      nb_loads = df_rep[
          df_rep["Destino"].str.contains("NB|LAREDO", case=False, na=False)
          & ~df_rep["Destino"].str.contains("EXPO", case=False, na=False)
      ].shape[0]
      total_loads = len(df_rep)

      df_agrupado = (
          df_rep.groupby("Unidad_Calc")["Millas_Calc"].sum().reset_index()
      )

      def clasificador_bucket(m):
        if m >= 3000:
          return "UNIDADES 3,000 + MILLAS"
        elif m >= 2500:
          return "UNIDADES 2,500 - 3,000 MILLAS"
        elif m >= 2000:
          return "UNIDADES 2,000-2,500 MILLAS"
        elif m >= 1500:
          return "UNIDADES 1,500 - 2,000 MILLAS"
        else:
          return "UNIDADES BAJO 1,500 MILLAS"

      df_agrupado["Categoria"] = df_agrupado["Millas_Calc"].apply(
          clasificador_bucket
      )
      conteo = df_agrupado["Categoria"].value_counts()

      t_3000 = conteo.get("UNIDADES 3,000 + MILLAS", 0)
      t_2500 = conteo.get("UNIDADES 2,500 - 3,000 MILLAS", 0)
      t_2000 = conteo.get("UNIDADES 2,000-2,500 MILLAS", 0)
      t_1500 = conteo.get("UNIDADES 1,500 - 2,000 MILLAS", 0)
      t_bajo = conteo.get("UNIDADES BAJO 1,500 MILLAS", 0)
      tot_uni = len(df_agrupado)

      df_res_loads = pd.DataFrame({
          "Categoría": ["EXPO DE NLD", "NB DE LAREDO", "VIAJES DE SB", "TOTAL LOADS"],
          "Cantidad": [expo_loads, nb_loads, sb_loads, total_loads],
      })

      df_res_target = pd.DataFrame({
          "TARGET DE UNIDADES MILLAS": [
              "TOTAL",
              "UNIDADES 3,000 + MILLAS",
              "UNIDADES 2,500 - 3,000 MILLAS",
              "UNIDADES 2,000-2,500 MILLAS",
              "UNIDADES 1,500 - 2,000 MILLAS",
              "UNIDADES BAJO 1,500 MILLAS",
          ],
          "3,000 MILLAS": [
              tot_uni,
              t_3000,
              t_2500,
              t_2000,
              t_1500,
              t_bajo,
          ],
      })

      st.markdown("### 🌟 Nuevos Indicadores Estratégicos Propuestos")
      c1, c2, c3 = st.columns(3)

      pct_meta = ((t_3000 + t_2500) / tot_uni * 100) if tot_uni > 0 else 0
      millas_totales = df_rep["Millas_Calc"].sum()
      promedio_millas = millas_totales / tot_uni if tot_uni > 0 else 0

      c1.metric(
          "Eficiencia de Meta (>2,500 mi)",
          f"{pct_meta:.1f}%",
          "Unidades rentables",
      )
      c2.metric("Total de St. Miles Generadas", f"{millas_totales:,.1f} mi")
      c3.metric("Promedio de Millas por Unidad", f"{promedio_millas:,.1f} mi")

      st.markdown("---")
      st.markdown("### 📊 Tablas de Resumen Generadas (Formato BSCF Oficial)")
      colA, colB = st.columns(2)
      with colA:
        st.markdown("**Desglose de Cargas**")
        st.dataframe(
            df_res_loads.set_index("Categoría"), use_container_width=True
        )
      with colB:
        st.markdown("**Target de Unidades Millas**")
        st.dataframe(
            df_res_target.set_index("TARGET DE UNIDADES MILLAS"),
            use_container_width=True,
        )

      st.markdown("---")
      st.subheader("📋 Vista Previa de los Datos del Archivo Subido")
      st.dataframe(df_rep, use_container_width=True)

# ==========================================
# PIE DE PÁGINA
# ==========================================
st.markdown("---")
st.caption("Sistema de Control Privado - Morgan Express © 2026")
        
