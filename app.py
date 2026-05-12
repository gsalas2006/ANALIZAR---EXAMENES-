import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Tablero Gerencial de Evaluaciones", layout="wide")

st.title("🏛️ Sistema de Gestión y Análisis de Exámenes")
st.markdown("Generación de reportes comparativos por temas y análisis psicométrico.")

# 1. CARGA DE ARCHIVOS
col_files = st.columns(2)
with col_files[0]:
    file_alu = st.file_uploader("📂 Resultados de Alumnos (Excel)", type=["xlsx"])
with col_files[1]:
    file_cla = st.file_uploader("🔑 Claves de Temas A y B (Excel)", type=["xlsx"])

if file_alu and file_cla:
    try:
        df_alumnos = pd.read_excel(file_alu)
        df_claves = pd.read_excel(file_cla)
        df_alumnos.columns = [str(c).strip() for c in df_alumnos.columns]
        
        # Diccionario de claves
        claves_dict = {
            'A': [str(x).strip().upper() for x in df_claves.iloc[1, 1:41].values],
            'B': [str(x).strip().upper() for x in df_claves.iloc[2, 1:41].values]
        }

        # Procesamiento
        def calificar(row):
            tema = str(row['TIPO']).strip().upper()
            if tema not in claves_dict: return row
            correctas = 0
            for i in range(1, 41):
                es_correcta = 1 if str(row[str(i)]).strip().upper() == claves_dict[tema][i-1] else 0
                row[f'p{i}_b'] = es_correcta
                correctas += es_correcta
            row['Nota'] = (correctas * 20) / 40
            row['Estado'] = 'APROBADO' if row['Nota'] >= 11 else 'DESAPROBADO'
            return row

        df_final = df_alumnos.apply(calificar, axis=1)

        # --- SECCIÓN DE PESTAÑAS (TABS) ---
        tab1, tab2, tab3, tab4 = st.tabs(["📊 Resumen Gerencial", "🅰️ Análisis Tema A", "🅱️ Análisis Tema B", "📜 Lista de Notas"])

        # PESTAÑA 1: RESUMEN GERENCIAL
        with tab1:
            st.subheader("Indicadores de Desempeño Global")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Alumnos Evaluados", len(df_final))
            c2.metric("Promedio General", f"{df_final['Nota'].mean():.2f}")
            c3.metric("Aprobados", len(df_final[df_final['Estado']=='APROBADO']))
            c4.metric("% Rendimiento", f"{(len(df_final[df_final['Estado']=='APROBADO'])/len(df_final))*100:.1f}%")
            
            # Comparativo de Temas
            st.divider()
            st.write("**Comparación por Temas:**")
            comparativo = df_final.groupby('TIPO')['Nota'].agg(['count', 'mean', 'max', 'min']).rename(columns={'count':'Alumnos', 'mean':'Promedio'})
            st.table(comparativo.style.format("{:.2f}", subset=['Promedio', 'max', 'min']))

        # FUNCIÓN PARA ANÁLISIS PSICOMÉTRICO POR TEMA
        def obtener_analisis_tema(df_tema):
            df_s = df_tema.sort_values(by='Nota', ascending=False)
            n_27 = int(len(df_s) * 0.27) or 1
            sup, inf = df_s.head(n_27), df_s.tail(n_27)
            res = []
            for i in range(1, 41):
                col_b = f'p{i}_b'
                dificultad = df_tema[col_b].mean()
                discrim = (sup[col_b].sum() - inf[col_b].sum()) / n_27
                res.append({"Pregunta": f"P{i}", "Dificultad %": dificultad*100, "Discriminación": discrim})
            return pd.DataFrame(res)

        # PESTAÑA 2 Y 3: ANÁLISIS POR TEMA
        df_a = df_final[df_final['TIPO'] == 'A']
        df_b = df_final[df_final['TIPO'] == 'B']

        with tab2:
            st.subheader("Calidad de Preguntas - Tema A")
            if not df_a.empty:
                st.dataframe(obtener_analisis_tema(df_a), use_container_width=True)
            else: st.info("No hay datos del Tema A")

        with tab3:
            st.subheader("Calidad de Preguntas - Tema B")
            if not df_b.empty:
                st.dataframe(obtener_analisis_tema(df_b), use_container_width=True)
            else: st.info("No hay datos del Tema B")

        # PESTAÑA 4: LISTA DE NOTAS
        with tab4:
            st.subheader("Relación Nominal de Estudiantes")
            st.dataframe(df_final[['DNI', 'TIPO', 'Nota', 'Estado']], use_container_width=True)

        # 5. DESCARGA UNIFICADA
        st.divider()
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_final.to_excel(writer, index=False, sheet_name='Lista_General')
            if not df_a.empty: obtener_analisis_tema(df_a).to_excel(writer, index=False, sheet_name='Analisis_Tema_A')
            if not df_b.empty: obtener_analisis_tema(df_b).to_excel(writer, index=False, sheet_name='Analisis_Tema_B')
            comparativo.to_excel(writer, sheet_name='Resumen_Gerencial')
        
        st.download_button(
            label="📥 DESCARGAR INFORME GERENCIAL (EXCEL)",
            data=output.getvalue(),
            file_name="Informe_Gerencial_Completo.xlsx",
            use_container_width=True
        )

    except Exception as e:
        st.error(f"Error en el procesamiento: {e}")
