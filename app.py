import streamlit as st
import pandas as pd
import io
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Analizador Pro - Anatomía", layout="wide")

# Estilo para que se vea moderno
st.markdown("""
    <style>
    .stMetric { background-color: #f8fafc; padding: 15px; border-radius: 10px; border: 1px solid #e2e8f0; }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 Dashboard Analítico de Evaluación de Anatomía")

# CARGA DE ARCHIVOS (Igual que antes)
col_f1, col_f2 = st.columns(2)
with col_f1: f_alu = st.file_uploader("📂 Resultados Alumnos", type=["xlsx"])
with col_f2: f_cla = st.file_uploader("🔑 Clave de Respuestas", type=["xlsx"])

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

        df_full = df_alumnos.apply(procesar, axis=1)
        df_limpio = df_full.drop(columns=[str(i) for i in range(1, 41)], errors='ignore')

        # --- SECCIÓN 1: MÉTRICAS RÁPIDAS ---
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Evaluados", len(df_limpio))
        m2.metric("Promedio General", round(df_limpio['Nota'].mean(), 2))
        m3.metric("% Aprobación", f"{(len(df_limpio[df_limpio['Estado']=='APROBADO'])/len(df_limpio))*100:.1f}%")
        m4.metric("Nota Máxima", df_limpio['Nota'].max())

        st.divider()

        # --- SECCIÓN 2: GRÁFICAS DE ALTO IMPACTO ---
        col_g1, col_g2 = st.columns(2)

        with col_g1:
            # Gráfico de Distribución (Histograma)
            fig_hist = px.histogram(df_limpio, x='Nota', color='TIPO', barmode='group',
                                   title="Distribución de Notas (Frecuencia)",
                                   color_discrete_sequence=['#3b82f6', '#a855f7'],
                                   labels={'Nota': 'Puntaje Obtenido'})
            st.plotly_chart(fig_hist, use_container_width=True)

        with col_g2:
            # Gráfico de Torta de Aprobados
            fig_pie = px.pie(df_limpio, names='Estado', hole=0.5,
                            title="Estado Final de los Estudiantes",
                            color='Estado', color_discrete_map={'APROBADO':'#10b981', 'DESAPROBADO':'#ef4444'})
            st.plotly_chart(fig_pie, use_container_width=True)

        st.divider()

        # --- SECCIÓN 3: PSICOMETRÍA VISUAL ---
        st.subheader("🎯 Análisis Psicométrico por Pregunta")
        
        def calc_psico_graf(df):
            res = []
            df_s = df.sort_values(by='Nota', ascending=False)
            n27 = int(len(df_s) * 0.27) or 1
            for i in range(1, 41):
                col = f'p{i}_b'
                dif = df[col].mean()
                dis = (df_s.head(n27)[col].sum() - df_s.tail(n27)[col].sum()) / n27
                res.append({"Pregunta": i, "Dificultad": round(dif, 2), "Discriminación": round(dis, 2)})
            return pd.DataFrame(res)

        df_psico = calc_psico_graf(df_full)
        
        # Gráfico de Dispersión (Scatter Plot)
        fig_scatter = px.scatter(df_psico, x="Dificultad", y="Discriminación", 
                                 text="Pregunta", size_max=60,
                                 title="Mapa de Calidad de Preguntas (Dificultad vs Discriminación)",
                                 labels={"Dificultad": "Índice de Facilidad (0 a 1)"})
        fig_scatter.add_hline(y=0.2, line_dash="dash", line_color="red", annotation_text="Mínimo aceptable")
        st.plotly_chart(fig_scatter, use_container_width=True)

        # BOTÓN DE DESCARGA
        st.download_button("📥 Descargar Reporte Completo", io.BytesIO().getvalue(), "Informe_Pro.xlsx")

    except Exception as e:
        st.error(f"Error: {e}")
