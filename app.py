import streamlit as st
import pandas as pd
import io
import plotly.express as px

st.set_page_config(page_title="Analizador Académico Ejecutivo", layout="wide")

st.title("🏛️ Sistema de Gestión y Análisis de Exámenes")
st.write("Generación de reportes ejecutivos con análisis psicométrico y comparativo.")

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

        # Procesamiento de Calificaciones
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

        # --- LIMPIEZA: Eliminamos las columnas de respuestas originales (1 a 40) ---
        columnas_a_borrar = [str(i) for i in range(1, 41)]
        df_final = df_procesado.drop(columns=columnas_a_borrar, errors='ignore')

        # Función para Análisis Psicométrico
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
                res.append({"Pregunta": f"P{i}", "Dificultad %": dif, "Discriminación": dis})
            return pd.DataFrame(res)

        df_a = df_procesado[df_procesado['TIPO'] == 'A']
        df_b = df_procesado[df_procesado['TIPO'] == 'B']
        psico_a = generar_psicometria(df_a)
        psico_b = generar_psicometria(df_b)
        resumen_gerencial = df_final.groupby('TIPO')['Nota'].agg(['count', 'mean', 'max', 'min']).reset_index()

        # --- DASHBOARD WEB ---
        tab_res, tab_gra, tab_psico = st.tabs(["📊 Resumen", "📈 Gráficas", "🎯 Psicometría"])
        
        with tab_res:
            m1, m2, m3 = st.columns(3)
            m1.metric("Total Alumnos", len(df_final))
            m2.metric("Promedio", round(df_final['Nota'].mean(), 2))
            m3.metric("% Aprobados", f"{(len(df_final[df_final['Estado']=='APROBADO'])/len(df_final))*100:.1f}%")
            st.table(resumen_gerencial)

        with tab_gra:
            c_g1, c_g2 = st.columns(2)
            c_g1.plotly_chart(px.pie(df_final, names='Estado', title="Aprobados vs Desaprobados", color_discrete_sequence=['#2ecc71', '#e74c3c']), use_container_width=True)
            c_g2.plotly_chart(px.histogram(df_final, x='Nota', title="Distribución de Notas", color_discrete_sequence=['#3498db']), use_container_width=True)

        with tab_psico:
            st.dataframe(psico_a, use_container_width=True)
            st.dataframe(psico_b, use_container_width=True)

        # --- EXCEL LIMPIO (Sin columnas 1-40) ---
        st.divider()
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            resumen_gerencial.to_excel(writer, index=False, sheet_name='Resumen_Gerencial')
            # Solo columnas clave para el reporte de notas
            df_final[['DNI', 'TIPO', 'Nota', 'Estado']].to_excel(writer, index=False, sheet_name='Lista_de_Notas')
            if not psico_a.empty: psico_a.to_excel(writer, index=False, sheet_name='Psicometria_Tema_A')
            if not psico_b.empty: psico_b.to_excel(writer, index=False, sheet_name='Psicometria_Tema_B')

        st.download_button(
            label="📥 DESCARGAR INFORME EJECUTIVO",
            data=output.getvalue(),
            file_name="Informe_Ejecutivo_Final.xlsx",
            use_container_width=True
        )

    except Exception as e:
        st.error(f"Error: {e}")
