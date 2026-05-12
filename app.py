import streamlit as st
import pandas as pd
import io
import plotly.express as px

st.set_page_config(page_title="Tablero de Control Académico", layout="wide")

st.title("🏛️ Sistema de Gestión y Análisis de Exámenes")

# 1. CARGA DE ARCHIVOS
col_f1, col_f2 = st.columns(2)
with col_f1:
    f_alu = st.file_uploader("📂 Resultados Alumnos (Excel)", type=["xlsx"])
with col_f2:
    f_cla = st.file_uploader("🔑 Clave de Respuestas (Excel)", type=["xlsx"])

if f_alu and f_cla:
    try:
        df_alumnos = pd.read_excel(f_alu)
        df_claves = pd.read_excel(f_cla)
        df_alumnos.columns = [str(c).strip() for c in df_alumnos.columns]
        
        claves = {
            'A': [str(x).strip().upper() for x in df_claves.iloc[1, 1:41].values],
            'B': [str(x).strip().upper() for x in df_claves.iloc[2, 1:41].values]
        }

        # PROCESAMIENTO
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
        # Limpiamos para el reporte (Sin columnas 1-40)
        df_limpio = df_full.drop(columns=[str(i) for i in range(1, 41)], errors='ignore')

        # PSICOMETRÍA UNIFICADA (TEMA A Y B)
        def calc_psico(df, label):
            if df.empty: return pd.DataFrame()
            df_s = df.sort_values(by='Nota', ascending=False)
            n27 = int(len(df_s) * 0.27) or 1
            sup, inf = df_s.head(n27), df_s.tail(n27)
            items = []
            for i in range(1, 41):
                col = f'p{i}_b'
                dif = df[col].mean() * 100
                dis = (sup[col].sum() - inf[col].sum()) / n27
                nivel = "FÁCIL" if dif > 70 else ("DIFÍCIL" if dif < 30 else "REGULAR")
                items.append({"Tema": label, "Pregunta": f"P{i}", "Dificultad %": round(dif,1), "Discriminación": round(dis,2), "Nivel": nivel})
            return pd.DataFrame(items)

        psico_final = pd.concat([calc_psico(df_full[df_full['TIPO']=='A'], "TEMA A"), 
                                 calc_psico(df_full[df_full['TIPO']=='B'], "TEMA B")])

        # RESUMEN PARA EL JEFE
        resumen = df_limpio.groupby('TIPO')['Nota'].agg(['count', 'mean', 'max', 'min']).reset_index()
        resumen.columns = ['Tema', 'Alumnos', 'Promedio', 'Nota Máx', 'Nota Mín']

        # --- DASHBOARD WEB ---
        t1, t2, t3 = st.tabs(["📈 Gráficas", "🎯 Calidad de Preguntas", "📋 Lista de Notas"])
        with t1:
            st.plotly_chart(px.pie(df_limpio, names='Estado', title="Tasa de Aprobación", color_discrete_sequence=['#2ecc71', '#e74c3c']))
            st.table(resumen)
        with t2:
            st.dataframe(psico_final, use_container_width=True)

        # --- EXPORTACIÓN PROFESIONAL (El Excel que pediste) ---
        st.divider()
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            # Hoja 1: El Resumen Gerencial
            resumen.to_excel(writer, index=False, sheet_name='RESUMEN_EJECUTIVO')
            # Hoja 2: La lista de alumnos limpia
            df_limpio[['DNI', 'TIPO', 'Nota', 'Estado']].to_excel(writer, index=False, sheet_name='NOTAS_ALUMNOS')
            # Hoja 3: Psicometría con colores
            psico_final.to_excel(writer, index=False, sheet_name='ANALISIS_CALIDAD')
            
            # Formatos de Excel
            book = writer.book
            sheet_psico = writer.sheets['ANALISIS_CALIDAD']
            
            fmt_red = book.add_format({'bg_color': '#FFC7CE', 'font_color': '#9C0006'})
            fmt_yel = book.add_format({'bg_color': '#FFEB9C', 'font_color': '#9C6500'})
            fmt_grn = book.add_format({'bg_color': '#C6EFCE', 'font_color': '#006100'})
            
            sheet_psico.conditional_format('E2:E81', {'type': 'cell', 'criteria': 'equal to', 'value': '"DIFÍCIL"', 'format': fmt_red})
            sheet_psico.conditional_format('E2:E81', {'type': 'cell', 'criteria': 'equal to', 'value': '"REGULAR"', 'format': fmt_yel})
            sheet_psico.conditional_format('E2:E81', {'type': 'cell', 'criteria': 'equal to', 'value': '"FÁCIL"', 'format': fmt_grn})

        st.download_button("📥 DESCARGAR INFORME GERENCIAL COMPLETO", output.getvalue(), "Reporte_Evaluacion_Profesional.xlsx", use_container_width=True)

    except Exception as e:
        st.error(f"Error: {e}")
