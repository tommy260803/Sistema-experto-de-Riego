import os
import streamlit as st
from components.tablero_control import render_dashboard
from components.simulador import render_simulator
from components.historico import render_historical
from components.informes import render_reports
from nucleo.utilidades import ensure_data_files

ensure_data_files()

st.set_page_config(page_title="🌱 Riego Inteligente", page_icon="🌊", layout="wide", initial_sidebar_state="expanded")

css_path = "assets/styles.css"
if os.path.exists(css_path):
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

with st.sidebar:
    logo_path = "assets/images/logo.png"
    if os.path.exists(logo_path):
        st.image(logo_path, caption="Riego Inteligente", use_column_width=True)
    else:
        st.markdown("### Riego Inteligente")
    if st.button("Acerca del Sistema"):
        st.info("Sistema experto de riego con Lógica Difusa (Mamdani) y visualizaciones educativas.")

tab1, tab2, tab3, tab4 = st.tabs([
    "🌊 Calculadora de Riego",
    "📊 Visualizaciones",
    "📈 Histórico y Análisis",
    "🎓 Simulador de Escenarios",
])

with tab1:
    render_dashboard()
with tab2:
    from nucleo.visualizacion import render_visualizations_page
    render_visualizations_page()
with tab3:
    render_historical()
with tab4:
    render_simulator()
