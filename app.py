# ==========================================
# NUEVA PESTAÑA SUSTITUIDA: GENERADOR BSCF DESDE LA NUBE (GOOGLE SHEETS/DRIVE)
# ==========================================
elif modo_analisis == "Generador de Resumen (Report_3.xlsx)":
    st.title("📊 Generador de Resumen Automático (BSCF)")
    st.markdown("Conectado directamente a la Base de Datos en la nube (Google Workspace). No se requiere carga manual.")
    
    # ---------------------------------------------------------
    # 🔗 AQUÍ PONES LA URL DE TU ARCHIVO EN GOOGLE DRIVE/SHEETS
    # ---------------------------------------------------------
    url_base_datos_reporte = "URL_DE_TU_NUEVO_GOOGLE_SHEET" 
    
    # Intento de lectura automatizada desde la nube
    with st.spinner("Sincronizando base de datos desde Google Drive..."):
        try:
            # Lee los datos usando la conexión que ya tienes configurada arriba
            # Nota: Si lo pusiste como una pestaña nueva en tu archivo actual, puedes usar:
            # df_rep = conn.read(spreadsheet=url_excel_agosto, worksheet="NombreDeTuPestaña")
            df_rep = conn.read(spreadsheet=url_base_datos_reporte)
            
            if df_rep.empty:
                st.warning("La base de datos está vacía o no se pudo leer. Verifica el enlace y los permisos.")
            else:
                st.success("¡Base de datos sincronizada correctamente en tiempo real!")
                
                # PROCESAMIENTO AUTOMATIZADO DE LA BASE
                df_rep.columns = df_rep.columns.astype(str).str.strip()
                
                # Omitir fila final de Totales si existe en el Excel
                if len(df_rep) > 0 and "Total" in str(df_rep.iloc[-1].values):
                    df_rep = df_rep.iloc[:-1].copy()
                    
                # 1. Extraer Millas (St. Miles)
                col_millas = None
                if "St. Miles" in df_rep.columns:
                    col_millas = "St. Miles"
                elif len(df_rep.columns) > 16:
                    col_millas = df_rep.columns[16]
                    
                if col_millas:
                    df_rep["Millas_Calc"] = pd.to_numeric(df_rep[col_millas], errors="coerce").fillna(0)
                else:
                    df_rep["Millas_Calc"] = 0
                    
                # 2. Extraer Unidades (Settl.#)
                col_unidad = None
                if "Settl.#" in df_rep.columns:
                    col_unidad = "Settl.#"
                elif len(df_rep.columns) > 1:
                    col_unidad = df_rep.columns[1]
                    
                if col_unidad:
                    df_rep["Unidad_Calc"] = df_rep[col_unidad].fillna("Vacía").astype(str).str.strip()
                else:
                    df_rep["Unidad_Calc"] = "Vacía"
                    
                # Filtro de unidades válidas
                df_rep = df_rep[df_rep["Unidad_Calc"].str.lower() != "nan"]
                    
                # 3. Extraer y Calcular Cargas (Loads / Destinos)
                if "Orig-Dest" in df_rep.columns:
                    df_rep[["Origen", "Destino"]] = df_rep["Orig-Dest"].str.split(" - ", n=1, expand=True)
                    df_rep["Destino"] = df_rep["Destino"].fillna("").astype(str)
                elif "Destino" not in df_rep.columns:
                    df_rep["Destino"] = ""
                    
                expo_loads = df_rep[df_rep["Destino"].str.contains("EXPO|NLD", case=False, na=False)].shape[0]
                sb_loads = df_rep[df_rep["Destino"].str.contains("SB", case=False, na=False)].shape[0]
                nb_loads = df_rep[df_rep["Destino"].str.contains("NB|LAREDO", case=False, na=False) & ~df_rep["Destino"].str.contains("EXPO", case=False, na=False)].shape[0]
                total_loads = len(df_rep)
                
                # 4. Agrupación por Unidad para generar el TARGET
                df_agrupado = df_rep.groupby("Unidad_Calc")["Millas_Calc"].sum().reset_index()
                
                def clasificador_bucket(m):
                    if m >= 3000: return "UNIDADES 3,000 + MILLAS"
                    elif m >= 2500: return "UNIDADES 2,500 - 3,000 MILLAS"
                    elif m >= 2000: return "UNIDADES 2,000-2,500 MILLAS"
                    elif m >= 1500: return "UNIDADES 1,500 - 2,000 MILLAS"
                    else: return "UNIDADES BAJO 1,500 MILLAS"
                    
                df_agrupado["Categoria"] = df_agrupado["Millas_Calc"].apply(clasificador_bucket)
                conteo = df_agrupado["Categoria"].value_counts()
                
                t_3000 = conteo.get("UNIDADES 3,000 + MILLAS", 0)
                t_2500 = conteo.get("UNIDADES 2,500 - 3,000 MILLAS", 0)
                t_2000 = conteo.get("UNIDADES 2,000-2,500 MILLAS", 0)
                t_1500 = conteo.get("UNIDADES 1,500 - 2,000 MILLAS", 0)
                t_bajo = conteo.get("UNIDADES BAJO 1,500 MILLAS", 0)
                tot_uni = len(df_agrupado)
                
                # --- CREACIÓN DE LAS TABLAS IDENTICAS A LA IMAGEN ---
                df_res_loads = pd.DataFrame({
                    "Categoría": ["EXPO DE NLD", "NB DE LAREDO", "VIAJES DE SB", "TOTAL LOADS"],
                    "Cantidad": [expo_loads, nb_loads, sb_loads, total_loads]
                })
                
                df_res_target = pd.DataFrame({
                    "TARGET DE UNIDADES MILLAS": [
                        "TOTAL", 
                        "UNIDADES 3,000 + MILLAS", 
                        "UNIDADES 2,500 - 3,000 MILLAS", 
                        "UNIDADES 2,000-2,500 MILLAS", 
                        "UNIDADES 1,500 - 2,000 MILLAS", 
                        "UNIDADES BAJO 1,500 MILLAS"
                    ],
                    "3,000 MILLAS": [tot_uni, t_3000, t_2500, t_2000, t_1500, t_bajo]
                })
                
                # --- NUEVOS INDICADORES PROPUESTOS ---
                st.markdown("### 🌟 Nuevos Indicadores Estratégicos Propuestos")
                c1, c2, c3 = st.columns(3)
                
                pct_meta = ((t_3000 + t_2500) / tot_uni * 100) if tot_uni > 0 else 0
                millas_totales = df_rep["Millas_Calc"].sum()
                promedio_millas = millas_totales / tot_uni if tot_uni > 0 else 0
                
                # Indicador 1: % de unidades que están en la zona verde (Rentabilidad)
                c1.metric("Eficiencia de Meta (>2,500 mi)", f"{pct_meta:.1f}%", "Unidades rentables")
                # Indicador 2: Producción total de millas en el reporte
                c2.metric("Total de St. Miles Generadas", f"{millas_totales:,.1f} mi")
                # Indicador 3: Millas promedio por unidad de la flotilla actual
                c3.metric("Promedio de Millas por Unidad", f"{promedio_millas:,.1f} mi")
                
                st.markdown("---")
                st.markdown("### 📊 Tablas de Resumen Generadas (Formato BSCF Oficial)")
                colA, colB = st.columns(2)
                with colA:
                    st.markdown("**Desglose de Cargas**")
                    st.dataframe(df_res_loads.set_index("Categoría"), use_container_width=True)
                with colB:
                    st.markdown("**Target de Unidades Millas**")
                    st.dataframe(df_res_target.set_index("TARGET DE UNIDADES MILLAS"), use_container_width=True)
                    
                st.markdown("---")
                st.subheader("📋 Vista Previa de los Datos Sincronizados de la Nube")
                st.dataframe(df_rep, use_container_width=True)
                
        except Exception as e:
            st.error(f"Error de conexión con la base de datos en la nube: {e}")
