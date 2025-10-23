from __future__ import annotations
import os
import io
from typing import Dict, List
import streamlit as st
from fpdf import FPDF
from src.knowledge_base import PLANT_KB
from src.utils import export_history_csv


class _PDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 14)
        self.cell(0, 10, "Sistema de Riego Inteligente - Informe", ln=1)
        self.ln(2)


def _pdf_section(pdf: _PDF, title: str, lines: List[str]) -> None:
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, title, ln=1)
    pdf.set_font("Arial", "", 10)
    for line in lines:
        pdf.multi_cell(0, 6, line)
    pdf.ln(3)


def generate_pdf_report(datos: Dict[str, float]) -> bytes:
    """Crear PDF con fpdf a partir de datos de contexto y decisión.

    datos esperados: {
      "planta": str, "temperatura": float, "humedad_suelo": float,
      "prob_lluvia": float, "humedad_ambiental": float, "viento": float,
      "tiempo_min": float, "frecuencia": float
    }
    """
    pdf = _PDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    _pdf_section(
        pdf,
        "Entradas",
        [
            f"Planta: {datos.get('planta','')}",
            f"Temperatura: {datos.get('temperatura',0)} °C",
            f"H. Suelo: {datos.get('humedad_suelo',0)} %",
            f"Prob. Lluvia: {datos.get('prob_lluvia',0)} %",
            f"H. Ambiental: {datos.get('humedad_ambiental',0)} %",
            f"Viento: {datos.get('viento',0)} km/h",
        ],
    )
    _pdf_section(
        pdf,
        "Decisión",
        [
            f"Tiempo recomendado: {float(datos.get('tiempo_min',0)):.1f} min",
            f"Frecuencia diaria: {float(datos.get('frecuencia',0)):.2f} veces",
        ],
    )
    kb = PLANT_KB.get(datos.get("planta", ""), {})
    _pdf_section(pdf, "Recomendaciones", [kb.get("consejos", "")])

    return pdf.output(dest="S").encode("latin1")


def render_reports() -> None:
    st.title("📚 Guía y Reportes")

    st.subheader("Generar reporte PDF")
    with st.form("pdf_form"):
        temperatura = st.number_input("Temperatura (°C)", 0.0, 45.0, 25.0)
        humedad_suelo = st.number_input("Humedad del Suelo (%)", 0.0, 100.0, 40.0)
        prob_lluvia = st.number_input("Probabilidad de Lluvia (%)", 0.0, 100.0, 10.0)
        humedad_ambiental = st.number_input("Humedad Ambiental (%)", 0.0, 100.0, 50.0)
        viento = st.number_input("Viento (km/h)", 0.0, 50.0, 5.0)
        planta = st.selectbox("Planta", list(PLANT_KB.keys()))
        tiempo_min = st.slider("Tiempo (min)", 0.0, 60.0, 20.0)
        frecuencia = st.slider("Frecuencia (x/día)", 0.0, 4.0, 2.0)
        submitted = st.form_submit_button("Generar PDF")

    if submitted:
        datos = {
            "planta": planta,
            "temperatura": float(temperatura),
            "humedad_suelo": float(humedad_suelo),
            "prob_lluvia": float(prob_lluvia),
            "humedad_ambiental": float(humedad_ambiental),
            "viento": float(viento),
            "tiempo_min": float(tiempo_min),
            "frecuencia": float(frecuencia),
        }
        pdf = generate_pdf_report(datos)
        st.success("Reporte generado")
        st.download_button(
            label="Descargar PDF",
            data=pdf,
            file_name="reporte_riego.pdf",
            mime="application/pdf",
        )

    st.markdown("---")
    st.subheader("Información educativa")
    st.write(
        "La lógica difusa modela conceptos cualitativos (bajo, medio, alto) con funciones de membresía. "
        "Un motor de inferencia combina reglas del tipo SI-ENTONCES para producir salidas, que se defuzzifican con el método del centroide."
    )
