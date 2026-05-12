import streamlit as st
import pandas as pd
import io
import plotly.express as px

st.set_page_config(page_title="Tablero Gerencial Pro", layout="wide")

st.title("🏛️ Sistema de Gestión y Análisis de Exámenes")

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

        df_final = df_alumnos.apply(calificar, axis=1).copy()

        # --- SECCIÓN DE PESTAÑAS ---
        tab_res, tab_gra, tab_psico, tab_lista = st.tabs(["📊 Resumen Gerencial", "📈 Gráficas", "🎯 Psicometría", "📜 Lista de Notas"])

        with tab_res:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Alumnos", len(df_final))
            c2.metric("Promedio", f"{df_final['Nota'].mean():.2f}")
            c3.metric("Aprobados", len(df_final[df_final['Estado']=='APROBADO']))
            c4.metric("% Rendimiento", f"{(len(df_final[df_final['Estado']=='APROBADO'])/len(df_final))*100:.1f}%")
            
            st.divider()
            comparativo = df_final.groupby('TIPO')['Nota'].agg(['count', 'mean', 'max']).rename(columns={'count':'Alumnos', 'mean':'Promedio'})
            st.write("**Resumen por Tema:**")
            st.table(comparativo)

        with tab_gra:
            st.subheader("Visualización de Resultados")
            col_g1, col_g2 = st.columns(2)

            with col_g1:
                # Gráfico de Torta - Aprobados vs Desaprobados
                fig_pie = px.pie(df_final, names='Estado', title='Distribución de Aprobados',
                                 color='Estado', color_discrete_map={'APROBADO':'#2ecc71', 'DESAPROBADO':'#e74c3c'})
                st.plotly_chart(fig_pie, use_container_width=True)

            with col_g2:
                # Histograma de Notas
                fig_hist = px.histogram(df_final, x='Nota', title='Frecuencia de Notas',
                                       nbins=10, color_discrete_sequence=['#3498db'])
                st.plotly_chart(fig_hist, use_container_width=True)

        with tab_psico:
            # Lógica simplificada de discriminación para visualizar
            st.subheader("Análisis de Dificultad por Pregunta")
            dificultad_lista = []
            for i in range(1, 41):
                dificultad_lista.append({'Pregunta': f'P{i}', 'Facilidad': df_final[f'p{i}_b'].mean()*100})
            df_dif = pd.DataFrame(dificultad_lista)
            
            fig_bar = px.bar(df_dif, x='Pregunta', y='Facilidad', title='¿Qué preguntas fueron más fáciles?',
                             labels={'Facilidad': '% de Aciertos'})
            st.plotly_chart(fig_bar, use_container_width=True)

        with tab_lista:
            st.dataframe(df_final[['DNI', 'TIPO', 'Nota', 'Estado']], use_container_width=True)

        # 5. DESCARGA
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_final.to_excel(writer, index=False, sheet_name='General')
            comparativo.to_excel(writer, sheet_name='Resumen')
        
        st.download_button("📥 DESCARGAR INFORME COMPLETO", output.getvalue(), "Reporte_Grafico.xlsx", use_container_width=True)

    except Exception as e:
        st.error(f"Error: {e}")
