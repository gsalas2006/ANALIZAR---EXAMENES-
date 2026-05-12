import streamlit as st
import pandas as pd
import io

# 1. CONFIGURACIÓN DE LA PÁGINA
st.set_page_config(page_title="Plataforma de Evaluación", layout="wide")

st.title("📊 Plataforma de Análisis Estadístico de Exámenes")
st.markdown("""
Esta herramienta procesa los resultados de exámenes de cualquier asignatura. 
Cargue el archivo de respuestas de los alumnos y la clave correspondiente para generar el reporte completo.
""")

# 2. CARGA DE ARCHIVOS
col1, col2 = st.columns(2)
with col1:
    file_alu = st.file_uploader("📂 Subir Examen (Respuestas Alumnos)", type=["xlsx"])
with col2:
    file_cla = st.file_uploader("🔑 Subir Clave de Respuestas", type=["xlsx"])

if file_alu and file_cla:
    try:
        # Lectura de datos
        df_alumnos = pd.read_excel(file_alu)
        df_claves = pd.read_excel(file_cla)
        
        # Limpieza de nombres de columnas
        df_alumnos.columns = [str(c).strip() for c in df_alumnos.columns]
        
        # Identificar claves (Asumiendo Fila 1 para Tema A y Fila 2 para Tema B en el Excel de claves)
        # Ajustamos para tomar las respuestas de las columnas 1 a 40
        claves_dict = {
            'A': [str(x).strip().upper() for x in df_claves.iloc[1, 1:41].values],
            'B': [str(x).strip().upper() for x in df_claves.iloc[2, 1:41].values]
        }

        # 3. PROCESAMIENTO LÓGICO
        def calificar(row):
            tema = str(row['TIPO']).strip().upper()
            if tema not in claves_dict:
                row['Nota'] = 0
                row['Estado'] = 'ERROR TIPO'
                return row
            
            correctas = 0
            respuestas_clave = claves_dict[tema]
            
            # Comparamos cada pregunta del 1 al 40
            for i in range(1, 41):
                col_pregunta = str(i)
                if col_pregunta in df_alumnos.columns:
                    es_correcta = 1 if str(row[col_pregunta]).strip().upper() == respuestas_clave[i-1] else 0
                    row[f'p{i}_b'] = es_correcta # Columna binaria (1 o 0)
                    correctas += es_correcta
            
            # Cálculo de nota sobre 20
            row['Nota'] = (correctas * 20) / 40
            row['Estado'] = 'APROBADO' if row['Nota'] >= 11 else 'DESAPROBADO'
            return row

        # Aplicamos la función a todo el dataset
        with st.spinner('Procesando calificaciones...'):
            df_final = df_alumnos.apply(calificar, axis=1)

        # 4. PANEL DE CONTROL (DASHBOARD)
        st.divider()
        st.subheader("📈 Resumen General de Resultados")
        
        m1, m2, m3, m4 = st.columns(4)
        total = len(df_final)
        aprobados = len(df_final[df_final['Estado'] == 'APROBADO'])
        promedio = df_final['Nota'].mean()
        
        m1.metric("Total Alumnos", total)
        m2.metric("Aprobados", aprobados)
        m3.metric("Desaprobados", total - aprobados)
        m4.metric("Nota Promedio", round(promedio, 2))

        # 5. EXPORTACIÓN DE DATOS (ARCHIVO COMPLETO)
        st.divider()
        st.subheader("💾 Descargar Resultados")
        st.info("El archivo descargable contiene todas las columnas originales, las correcciones por pregunta, la nota final y el estado.")
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            # Aquí exportamos df_final completo para que no falte ninguna columna
            df_final.to_excel(writer, index=False, sheet_name='Reporte_Completo')
        
        st.download_button(
            label="📥 Descargar Excel con Todos los Datos",
            data=output.getvalue(),
            file_name="Reporte_Final_Evaluacion.xlsx",
            mime="application/vnd.ms-excel"
        )

    except Exception as e:
        st.error(f"Se detectó un error al procesar los archivos: {e}")
        st.warning("Asegúrese de que el archivo de alumnos tenga las columnas del 1 al 40 y la columna 'TIPO'.")
