"""
Configuración Centralizada para el Sistema de Visualización
Configuraciones compartidas entre todos los visualizadores
"""

from __future__ import annotations
from typing import Dict, List
try:
    import plotly.colors
    import plotly.express as px
except ImportError:
    # Fallback if plotly not available
    px = None


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
            'viridis': plotly.colors.sequential.Viridis,
            'plasma': plotly.colors.sequential.Plasma,
        }
        return scales.get(name, scales['blue'])
