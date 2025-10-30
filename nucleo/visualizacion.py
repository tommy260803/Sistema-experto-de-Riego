"""
Sistema de Visualización para Control de Riego Difuso
Módulo legado - ver nucleo/visualizadores/ para la nueva estructura modular
"""

from __future__ import annotations
from typing import Dict, List, Tuple, Optional
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import streamlit as st
from datetime import datetime, timedelta

from .motor_difuso import SistemaRiegoDifuso
from .base_conocimientos import PLANT_KB


# ========================= CONFIGURACIÓN GLOBAL =========================

class VisualizationConfig:
    """Configuración centralizada de estilos y colores"""

    # Paleta de colores profesional
    COLORS = {
        'primary': '#2E86AB',      # Azul profesional
        'secondary': '#A23B72',    # Magenta elegante
        'success': '#06A77D',      # Verde éxito
        'warning': '#F18F01',      # Naranja alerta
        'danger': '#C73E1D',       # Rojo peligro
        'info': '#6A4C93',         # Púrpura información
        'light': '#F5F5F5',        # Gris claro
        'dark': '#2D3142',         # Gris oscuro

        # Escalas para membership functions
        'bajo': '#3498DB',         # Azul
        'medio': '#F39C12',        # Naranja
        'alto': '#E74C3C',         # Rojo
        'nulo': '#95A5A6',         # Gris

        # Gradientes
        'gradient_blue': ['#E3F2FD', '#2196F3', '#0D47A1'],
        'gradient_green': ['#E8F5E9', '#4CAF50', '#1B5E20'],
        'gradient_red': ['#FFEBEE', '#F44336', '#B71C1C'],
    }

    # Estilos de gráficos
    LAYOUT_TEMPLATE = 'plotly_white'
    FONT_FAMILY = 'Segoe UI, Roboto, Arial, sans-serif'
    TITLE_FONT_SIZE = 18
    AXIS_FONT_SIZE = 12
    LEGEND_FONT_SIZE = 11

    # Dimensiones
    DEFAULT_HEIGHT = 450
    SURFACE_HEIGHT = 600
    DASHBOARD_HEIGHT = 400

    @staticmethod
    def get_color_scale(name: str = 'blue') -> List[str]:
        """Retorna escala de colores según nombre"""
        scales = {
            'blue': ['#E3F2FD', '#90CAF9', '#42A5F5', '#1E88E5', '#1565C0'],
            'green': ['#E8F5E9', '#A5D6A7', '#66BB6A', '#43A047', '#2E7D32'],
            'red': ['#FFEBEE', '#EF9A9A', '#E57373', '#EF5350', '#E53935'],
            'purple': ['#F3E5F5', '#CE93D8', '#AB47BC', '#8E24AA', '#6A1B9A'],
            'viridis': px.colors.sequential.Viridis,
            'plasma': px.colors.sequential.Plasma,
        }
        return scales.get(name, scales['blue'])


class FuzzyVisualizer:
    """Visualizador principal del sistema de riego difuso"""

    def __init__(self, system: Optional[SistemaRiegoDifuso] = None):
        self.system = system or SistemaRiegoDifuso()
        self.config = VisualizationConfig()

    def _setup_page_config(self):
        """Configura estilos CSS personalizados"""
        st.markdown("""
        <style>
        /* Estilo general - ajustar padding para evitar overlap con header */
        .main .block-container {
            padding-top: 0rem;
            padding-bottom: 2rem;
            margin-top: 0rem;
        }

        /* Títulos */
        h1, h2, h3 {
            font-family: 'Segoe UI', sans-serif;
            color: #2D3142;
        }

        /* Métricas */
        [data-testid="stMetricValue"] {
            font-size: 28px;
            font-weight: 600;
        }

        /* Tarjetas */
        .card {
            background: white;
            padding: 1.5rem;
            border-radius: 10px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            margin: 1rem 0;
        }

        /* Dividers */
        hr {
            margin: 2rem 0;
            border: none;
            height: 2px;
            background: linear-gradient(to right, transparent, #2E86AB, transparent);
        }
        </style>
        """, unsafe_allow_html=True)

    # ===================== FUNCIONES DE MEMBRESÍA =====================

    def plot_membership_functions_enhanced(self) -> None:
        """Visualización mejorada de funciones de membresía"""
        st.info("♻️Funcionalidad legacy simplificada. Use el sistema modular para características completas.")
        st.markdown("Para acceso completo, importe desde `nucleo.visualizadores`")

    # ===================== FUNCIONES SIMPLIFICADAS =====================

    def render_main_dashboard(self, inputs: Dict[str, float], outputs: Dict[str, float]) -> None:
        """Dashboard simplificado legacy"""
        st.title("🌊 Sistema de Riego Inteligente - Legacy")
        st.info("🆕 Sistema Modular Disponible - Use `from nucleo.visualizadores import render_visualizations_page`")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("⏱️ Tiempo", f"{outputs.get('tiempo', 0):.1f} min")
        with col2:
            st.metric("🔄 Frecuencia", f"{outputs.get('frecuencia', 0):.1f} x/día")
        with col3:
            st.metric("🌡️ Temperatura", f"{inputs.get('temperature', 25):.1f}°C")
        with col4:
            st.metric("🌱 Humedad", f"{inputs.get('soil_humidity', 50):.1f}%")


# ========================= FUNCIÓN PRINCIPAL =========================

def render_visualizations_page() -> None:
    """Versión simplificada legacy"""
    st.title("📊 Visualizaciones (Legacy)")
    st.info("🆕 **Sistema Modular Disponible**: Use `from nucleo.visualizadores import render_visualizations_page`")
    st.warning("Esta versión legacy tiene funcionalidad limitada.")

    # Basic visualization
    try:
        visualizer = FuzzyVisualizer()
        visualizer._setup_page_config()
        st.info("📚 La funcionalidad completa está disponible en el sistema modular")
    except Exception as e:
        st.error(f"Error en sistema legacy: {e}")


# ========================= FUNCIONES LEGACY (COMPATIBILIDAD) =========================

def plot_membership_functions(system=None):
    """Legacy function"""
    st.info("📚 Use el nuevo sistema modular para mejor funcionalidad")

def plot_reglas_activadas(activaciones=None):
    """Legacy function"""
    st.info("📚 Use el nuevo sistema modular para mejor funcionalidad")

def plot_gauge(valor=0.0, max_val=100.0, title=""):
    """Legacy function"""
    st.info("📚 Use el nuevo sistema modular para mejor funcionalidad")

def radar_inputs(vals=None):
    """Legacy function"""
    st.info("📚 Use el nuevo sistema modular para mejor funcionalidad")

def plot_surface_3d(var1="temp", var2="humedad", output="tiempo"):
    """Legacy function"""
    st.info("📚 Use el nuevo sistema modular para mejor funcionalidad")

def plot_comparacion_plantas():
    """Legacy function"""
    st.info("📚 Use el nuevo sistema modular para mejor funcionalidad")

def plot_historico(df=None):
    """Legacy function"""
    st.info("📚 Use el nuevo sistema modular para mejor funcionalidad")
