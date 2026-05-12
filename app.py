import streamlit as st
import pandas as pd
import io
import plotly.express as px

st.set_page_config(page_title="Analizador Académico Premium", layout="wide")

st.title("🏛️ Sistema de Gestión y Análisis de Exámenes")
st.write("Cargue los archivos para generar el Dashboard y el Informe Excel Profesional.")

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
        
        claves_dict = {
            'A': [str(x).strip().upper() for x in df_claves.iloc[1, 1:41].values],
            'B': [str(x).strip().upper() for x in df_claves.iloc[2, 1:41].values]
        }

        # PROCESAMIENTO
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

        df_procesado = df_alumnos.apply(calificar, axis=1)
        
        # Eliminar respuestas individuales (columnas 1-40)
        columnas_respuestas = [str(i) for i in range(1, 41)]
        df_final = df_procesado.drop(columns=columnas_respuestas, errors='ignore')

        # PSICOMETRÍA POR TEMA
        def generar_psicometria(df_tema):
            if df_tema.empty: return pd.DataFrame()
            df_s = df_tema.sort_values(by='Nota', ascending=False)
            n_27 = int(len(df_s) * 0.27) or 1
            sup, inf = df_s.head(n_27), df_s.tail(n_27)
            res = []
            for i in range(1, 41):
                col_b = f'p{i}_b'
                dif = df_tema[col_b].mean() * 100
                dis = (sup[col_b].sum() - inf[col_b].sum()) / n_27
                res.append({"Pregunta": f"P{i}", "Dificultad %": round(dif, 1), "Discriminación": round(dis, 2)})
            df_p = pd.DataFrame(res)
            df_p['Calidad'] = df_p['Discriminación'].apply(lambda x: 'Excelente' if x > 0.39 else ('Buena' if x >= 0.20 else 'Revisar'))
            return df_p

        df_a = df_procesado[df_procesado['TIPO'] == 'A']
        df_b = df_procesado[df_procesado['TIPO'] == 'B']
        psico_a = generar_psicometria(df_a)
        psico_b = generar_psicometria(df_b)
        resumen_gerencial = df_final.groupby('TIPO')['Nota'].agg(['count', 'mean', 'max', 'min']).reset_index()
        resumen_gerencial.columns = ['Tema', 'Total Alumnos', 'Nota Promedio', 'Nota Máxima', 'Nota Mínima']

        # --- DASHBOARD WEB ---
        tab1, tab2, tab3 = st.tabs(["📊 Dashboard Ejecutivo", "📈 Gráficas", "🎯 Psicometría"])
        with tab1:
            st.subheader("Indicadores Gerenciales")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Alumnos", len(df_final))
            m2.metric("Promedio", round(df_final['Nota'].mean(), 2))
            m3.metric("Aprobados", len(df_final[df_final['Estado']=='APROBADO']))
            m4.metric("% Rendimiento", f"{(len(df_final[df_final['Estado']=='APROBADO'])/len(df_final))*100:.1f}%")
            st.table(resumen_gerencial)

        with tab2:
            c1, c2 = st.columns(2)
            c1.plotly_chart(px.pie(df_final, names='Estado', title="Aprobados vs Desaprobados", color_discrete_sequence=['#2ecc71', '#e74c3c']), use_container_width=True)
            c2.plotly_chart(px.histogram(df_final, x='Nota', title="Frecuencia de Notas", color_discrete_sequence=['#3498db']), use_container_width=True)

        with tab3:
            st.write("**Calidad del Examen (Índice de Discriminación)**")
            st.dataframe(psico_a, use_container_width=True)

        # --- EXPORTACIÓN PROFESIONAL A EXCEL ---
        st.divider()
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            # 1. Hoja de Resumen (Con formato de tabla)
            resumen_gerencial.to_excel(writer, index=False, sheet_name='RESUMEN_GERENCIAL')
            
            # 2. Hoja de Notas (Limpia)
            df_final[['DNI', 'TIPO', 'Nota', 'Estado']].to_excel(writer, index=False, sheet_name='LISTA_DE_NOTAS')
            
            # 3. Psicometría
            if not psico_a.empty: psico_a.to_excel(writer, index=False, sheet_name='PSICOMETRIA_TEMA_A')
            if not psico_b.empty: psico_b.to_excel(writer, index=False, sheet_name='PSICOMETRIA_TEMA_B')
            
            # Formatear el Excel con estilos profesionales
            workbook = writer.book
            header_format = workbook.add_format({'bold': True, 'bg_color': '#4F81BD', 'font_color': 'white', 'border': 1})
            
            for sheet in writer.sheets.values():
                sheet.set_column('A:Z', 20) # Ajustar ancho de columnas

        st.download_button(
            label="📥 DESCARGAR INFORME EJECUTIVO PROFESIONAL",
            data=output.getvalue(),
            file_name="Reporte_Gerencial_Final.xlsx",
            use_container_width=True
        )

    except Exception as e:
        st.error(f"Error: {e}")
