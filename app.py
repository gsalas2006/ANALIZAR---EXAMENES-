import streamlit as st
import pandas as pd
import io
import plotly.express as px

st.set_page_config(page_title="Analizador Académico Pro", layout="wide")

st.title("📊 Dashboard de Análisis: Temas A y B")

# 1. CARGA DE ARCHIVOS
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

        # PROCESAMIENTO DE DATOS
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

        # FUNCIÓN PARA CALCULAR PSICOMETRÍA CON COLORES
        def obtener_analisis(df_tema, label):
            if df_tema.empty: return pd.DataFrame()
            df_s = df_tema.sort_values(by='Nota', ascending=False)
            n27 = int(len(df_s) * 0.27) or 1
            res = []
            for i in range(1, 41):
                col = f'p{i}_b'
                dif = df_tema[col].mean() * 100
                dis = (df_s.head(n27)[col].sum() - df_s.tail(n27)[col].sum()) / n27
                
                # Definir color y nivel
                color = "🟢" if dif > 70 else ("🔴" if dif < 30 else "🟡")
                nivel = "Fácil" if dif > 70 else ("Difícil" if dif < 30 else "Regular")
                
                res.append({"Pregunta": f"P{i}", "Dificultad %": round(dif, 1), 
                            "Discriminación": round(dis, 2), "Nivel": nivel, "Semáforo": color})
            return pd.DataFrame(res)

        df_psico_a = obtener_analisis(df_full[df_full['TIPO']=='A'], "A")
        df_psico_b = obtener_analisis(df_full[df_full['TIPO']=='B'], "B")

        # --- VISUALIZACIÓN ---
        st.subheader("📈 Análisis de Reactivos por Tema")
        c1, c2 = st.columns(2)

        with c1:
            st.markdown("### **TEMA A**")
            # Gráfica de barras de dificultad
            fig_a = px.bar(df_psico_a, x='Pregunta', y='Dificultad %', color='Dificultad %',
                           color_continuous_scale='RdYlGn', range_color=[0, 100])
            st.plotly_chart(fig_a, use_container_width=True)
            st.dataframe(df_psico_a, use_container_width=True, height=400)

        with c2:
            st.markdown("### **TEMA B**")
            # Gráfica de barras de dificultad
            fig_b = px.bar(df_psico_b, x='Pregunta', y='Dificultad %', color='Dificultad %',
                           color_continuous_scale='RdYlGn', range_color=[0, 100])
            st.plotly_chart(fig_b, use_container_width=True)
            st.dataframe(df_psico_b, use_container_width=True, height=400)

        # BOTÓN DE DESCARGA (EXCEL CON COLORES)
        st.divider()
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_full[['DNI', 'TIPO', 'Nota', 'Estado']].to_excel(writer, index=False, sheet_name='NOTAS')
            df_resumen = pd.concat([df_psico_a.assign(Tema='A'), df_psico_b.assign(Tema='B')])
            df_resumen.to_excel(writer, index=False, sheet_name='PSICOMETRIA')
            
            # Formatos para el Excel
            book = writer.book
            sheet = writer.sheets['PSICOMETRIA']
            f_red = book.add_format({'bg_color': '#FFC7CE'})
            f_yel = book.add_format({'bg_color': '#FFEB9C'})
            f_grn = book.add_format({'bg_color': '#C6EFCE'})
            
            sheet.conditional_format('D2:D81', {'type': 'cell', 'criteria': 'equal to', 'value': '"Difícil"', 'format': f_red})
            sheet.conditional_format('D2:D81', {'type': 'cell', 'criteria': 'equal to', 'value': '"Regular"', 'format': f_yel})
            sheet.conditional_format('D2:D81', {'type': 'cell', 'criteria': 'equal to', 'value': '"Fácil"', 'format': f_grn})

        st.download_button("📥 DESCARGAR REPORTE EJECUTIVO", output.getvalue(), "Reporte_Colores.xlsx", use_container_width=True)

    except Exception as e:
        st.error(f"Error: {e}")
