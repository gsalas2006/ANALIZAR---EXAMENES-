import streamlit as st
import pandas as pd
import io

# 1. CONFIGURACIÓN PROFESIONAL
st.set_page_config(page_title="Sistema de Evaluación", layout="wide")

st.title("📊 Plataforma de Análisis Estadístico")
st.write("Seleccione los archivos de resultados y claves para iniciar el análisis del examen.")

# 2. CARGA DE ARCHIVOS
col1, col2 = st.columns(2)
with col1:
    file_alu = st.file_uploader("📂 Subir Examen (Respuestas Alumnos)", type=["xlsx"])
with col2:
    file_cla = st.file_uploader("🔑 Subir Clave de Respuestas", type=["xlsx"])

if file_alu and file_cla:
    try:
        df_alumnos = pd.read_excel(file_alu)
        df_claves = pd.read_excel(file_cla)
        df_alumnos.columns = [str(c).strip() for c in df_alumnos.columns]
        
        # Identificar claves (Fila 1=A, Fila 2=B)
        claves_dict = {
            'A': [str(x).strip().upper() for x in df_claves.iloc[1, 1:41].values],
            'B': [str(x).strip().upper() for x in df_claves.iloc[2, 1:41].values]
        }

        # 3. PROCESAMIENTO
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

        # 4. DASHBOARD DE RESULTADOS
        st.divider()
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Alumnos", len(df_final))
        m2.metric("Aprobados", len(df_final[df_final['Estado'] == 'APROBADO']))
        m3.metric("Promedio General", round(df_final['Nota'].mean(), 2))

        # 5. BOTÓN DE DESCARGA UNIVERSAL
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_final[['DNI', 'TIPO', 'Nota', 'Estado']].to_excel(writer, index=False, sheet_name='Resultados')
        
        st.download_button(
            label="📥 Descargar Reporte Final de Evaluación",
            data=output.getvalue(),
            file_name="Reporte_Final_Evaluacion.xlsx",
            mime="application/vnd.ms-excel"
        )
    except Exception as e:
        st.error(f"Error: Verifique que los archivos tengan el formato correcto. {e}")
