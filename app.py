import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Análisis Anatomía", layout="wide")

st.title("🩺 Sistema de Calificación y Psicometría")
st.write("Sube los archivos para procesar los resultados de Anatomía Humana.")

# Carga de archivos
file_alu = st.file_uploader("Subir Examen (Alumnos)", type=["xlsx"])
file_cla = st.file_uploader("Subir Clave de Respuestas", type=["xlsx"])

if file_alu and file_cla:
    try:
        df_alumnos = pd.read_excel(file_alu)
        df_claves = pd.read_excel(file_cla)
        df_alumnos.columns = [str(c).strip() for c in df_alumnos.columns]
        
        # Lógica de Claves
        claves_dict = {
            'A': [str(x).strip().upper() for x in df_claves.iloc[1, 1:41].values],
            'B': [str(x).strip().upper() for x in df_claves.iloc[2, 1:41].values]
        }

        # Procesamiento
        def calificar(row):
            tema = str(row['TIPO']).strip().upper()
            if tema not in claves_dict: return row
            aciertos = sum(1 for i in range(1, 41) if str(row[str(i)]).strip().upper() == claves_dict[tema][i-1])
            row['Nota'] = (aciertos * 20) / 40
            row['Estado'] = 'APROBADO' if row['Nota'] >= 11 else 'DESAPROBADO'
            # Para discriminación
            for i in range(1, 41):
                row[f'p{i}_b'] = 1 if str(row[str(i)]).strip().upper() == claves_dict[tema][i-1] else 0
            return row

        df_final = df_alumnos.apply(calificar, axis=1)

        # Mostrar métricas
        st.success("✅ ¡Procesamiento completado!")
        c1, c2, c3 = st.columns(3)
        c1.metric("Alumnos", len(df_final))
        c2.metric("Aprobados", len(df_final[df_final['Estado'] == 'APROBADO']))
        c3.metric("Promedio", round(df_final['Nota'].mean(), 2))

        # Generar Excel para descarga
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_final[['DNI', 'TIPO', 'Nota', 'Estado']].to_excel(writer, index=False, sheet_name='Notas')
        
        st.download_button(
            label="📥 Descargar Reporte en Excel",
            data=output.getvalue(),
            file_name="Reporte_Anatomia.xlsx",
            mime="application/vnd.ms-excel"
        )
    except Exception as e:
        st.error(f"Error en los archivos: {e}")
