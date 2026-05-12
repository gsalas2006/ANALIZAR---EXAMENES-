import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Analizador Psicométrico", layout="wide")

st.title("📊 Plataforma de Análisis Estadístico y Psicométrico")
st.write("Cargue los archivos para obtener el reporte de notas y el análisis de calidad de preguntas.")

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
        
        claves_dict = {
            'A': [str(x).strip().upper() for x in df_claves.iloc[1, 1:41].values],
            'B': [str(x).strip().upper() for x in df_claves.iloc[2, 1:41].values]
        }

        # 1. CALIFICACIÓN
        def calificar(row):
            tema = str(row['TIPO']).strip().upper()
            if tema not in claves_dict: return row
            correctas = 0
            for i in range(1, 41):
                es_correcta = 1 if str(row[str(i)]).strip().upper() == claves_dict[tema][i-1] else 0
                row[f'p{i}_b'] = es_correcta
                correctas += es_correcta
            row['Nota'] = (correctas * 20) / 40
            return row

        df_final = df_alumnos.apply(calificar, axis=1)

        # 2. CÁLCULO PSICOMÉTRICO (Discriminación y Dificultad)
        # Dividimos en tercio superior e inferior por nota
        df_sorted = df_final.sort_values(by='Nota', ascending=False)
        n_27 = int(len(df_sorted) * 0.27) or 1
        superior = df_sorted.head(n_27)
        inferior = df_sorted.tail(n_27)

        analisis_preguntas = []
        for i in range(1, 41):
            col_b = f'p{i}_b'
            dificultad = df_final[col_b].mean() # % de aciertos
            # Discriminación: (Aciertos Superior - Aciertos Inferior) / N_grupo
            discrim = (superior[col_b].sum() - inferior[col_b].sum()) / n_27
            
            analisis_preguntas.append({
                'Pregunta': i,
                'Dificultad (%)': round(dificultad * 100, 1),
                'Discriminación': round(discrim, 2),
                'Calidad': "Excelente" if discrim > 0.39 else "Revisar" if discrim < 0.20 else "Buena"
            })
        
        df_psico = pd.DataFrame(analisis_preguntas)

        # 3. MOSTRAR RESULTADOS
        st.divider()
        st.subheader("⚠️ Análisis de Calidad de Preguntas")
        
        # Mostramos las preguntas con discriminación baja o negativa
        criticas = df_psico[df_psico['Discriminación'] < 0.20]
        if not criticas.empty:
            st.warning(f"Se detectaron {len(criticas)} preguntas con baja discriminación. Se sugiere revisarlas.")
            st.dataframe(criticas)
        else:
            st.success("¡Excelente! Todas las preguntas discriminan correctamente a los alumnos.")

        # 4. DESCARGA DE REPORTES
        st.divider()
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_final.to_excel(writer, index=False, sheet_name='Notas_Alumnos')
            df_psico.to_excel(writer, index=False, sheet_name='Analisis_Psicometrico')
        
        st.download_button(
            label="📥 Descargar Reporte Completo (Notas + Psicometría)",
            data=output.getvalue(),
            file_name="Analisis_Evaluacion_Completo.xlsx"
        )

    except Exception as e:
        st.error(f"Error técnico: {e}")
