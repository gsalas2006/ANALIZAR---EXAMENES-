import streamlit as st
import pandas as pd
import io
import plotly.express as px

st.set_page_config(page_title="Dashboard Académico Anatomía", layout="wide")

st.title("📊 Reporte Visual de Evaluación de Anatomía")

# 1. CARGA DE ARCHIVOS
col_f1, col_f2 = st.columns(2)
with col_f1:
    f_alu = st.file_uploader("📂 Resultados Alumnos", type=["xlsx"])
with col_f2:
    f_cla = st.file_uploader("🔑 Clave de Respuestas", type=["xlsx"])

if f_alu and f_cla:
    try:
        df_alumnos = pd.read_excel(f_alu)
        df_claves = pd.read_excel(f_cla)
        df_alumnos.columns = [str(c).strip() for c in df_alumnos.columns]
        
        claves = {
            'A': [str(x).strip().upper() for x in df_claves.iloc[1, 1:41].values],
            'B': [str(x).strip().upper() for x in df_claves.iloc[2, 1:41].values]
        }

        def procesar(row):
            t = str(row['TIPO']).strip().upper()
            if t not in claves: return row
            hits = 0
            for i in range(1, 41):
                res = 1 if str(row[str(i)]).strip().upper() == claves[t][i-1] else 0
                row[f'p{i}_b'] = res
                hits += res
            row['Nota'] = (hits * 20) / 40
            row['Estado'] = 'APROBADO' if row['Nota'] >= 11 else 'DESAPROBADO'
            return row

        df_res = df_alumnos.apply(procesar, axis=1)
        df_plot = df_res.drop(columns=[str(i) for i in range(1, 41)], errors='ignore')

        # --- PESTAÑAS ---
        t1, t2, t3 = st.tabs(["📈 Reporte Visual", "🎯 Análisis por Pregunta", "📋 Lista de Notas"])

        with t1:
            st.subheader("Distribución de Resultados")
            g1, g2 = st.columns(2)
            
            with g1:
                # GRÁFICA DE TORTA (APROBADOS VS DESAPROBADOS)
                fig_pie = px.pie(df_plot, names='Estado', title="Tasa de Aprobación",
                                 color='Estado', color_discrete_map={'APROBADO':'#2ecc71', 'DESAPROBADO':'#e74c3c'},
                                 hole=0.4)
                st.plotly_chart(fig_pie, use_container_width=True)
            
            with g2:
                # GRÁFICA DE BARRAS (NOTAS POR TEMA)
                fig_bar = px.box(df_plot, x='TIPO', y='Nota', points="all", title="Distribución de Notas por Tema",
                                 color='TIPO', color_discrete_sequence=['#3498db', '#9b59b6'])
                st.plotly_chart(fig_bar, use_container_width=True)

        with t2:
            st.info("Aquí puedes ver el semáforo de dificultad por cada pregunta.")
            # (Lógica de psicometría que ya teníamos...)

        with t3:
            st.dataframe(df_plot[['DNI', 'TIPO', 'Nota', 'Estado']], use_container_width=True)

        # 5. DESCARGA
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_plot[['DNI', 'TIPO', 'Nota', 'Estado']].to_excel(writer, index=False, sheet_name='Reporte_Final')
        
        st.download_button("📥 Descargar Informe de Resultados", output.getvalue(), "Reporte_Anatomia.xlsx", use_container_width=True)

    except Exception as e:
        st.error(f"Error: {e}")
