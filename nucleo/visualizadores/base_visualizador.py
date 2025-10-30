"""
Clase Base del Sistema de Visualización
Contiene la estructura principal del FuzzyVisualizer y métodos compartidos
"""

from __future__ import annotations
from typing import Dict, List, Tuple, Optional
import numpy as np

try:
    import streamlit as st
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
except ImportError as e:
    raise ImportError(f"Missing required packages: {e}")

from .configuracion import VisualizationConfig
from ..motor_difuso import SistemaRiegoDifuso
from .pertenencia import VisualizadorPertenencia
from .superficies import VisualizadorSuperficies
from .reglas import VisualizadorReglas
from .plantas import VisualizadorPlantas
from .sensibilidad import VisualizadorSensibilidad

from .tablero import RenderizadorTablero

# Import theme system
try:
    from components.theme_toggle import ThemeToggle
    THEME_SUPPORT = True
except ImportError:
    THEME_SUPPORT = False


class FuzzyVisualizer:
    """
    Visualizador principal del sistema de riego difuso
    Coordina todos los visualizadores especializados
    """

    def __init__(self, system: Optional[SistemaRiegoDifuso] = None):
        """
        Inicializa el visualizador

        Args:
            system: Instancia del sistema de riego difuso
        """
        self.system = system or SistemaRiegoDifuso()
        self.config = VisualizationConfig()
        self._update_theme_colors()  # Actualizar colores según tema actual

        # Inicializar visualizadores especializados disponibles
        self.membership_viz = VisualizadorPertenencia(self.system, self.config)
        self.surface_viz = VisualizadorSuperficies(self.system, self.config)
        self.rule_viz = VisualizadorReglas(self.system, self.config)
        self.plant_viz = VisualizadorPlantas(self.config)
        self.sensitivity_viz = VisualizadorSensibilidad(self.system, self.config)

        self.dashboard_viz = RenderizadorTablero(self.system, self.config)

        self._setup_page_config()

    def _update_theme_colors(self) -> None:
        """Actualiza colores de configuración según tema actual"""
        if THEME_SUPPORT and 'theme' in st.session_state:
            # Actualizar la configuración con colores del tema
            ThemeToggle.update_visualization_config(self.config)

    def _setup_page_config(self):
        """Configura estilos CSS adaptativos al tema"""
        # Los estilos se manejan completamente por ThemeToggle.inject_theme_css()
        # No agregar estilos estáticos aquí para evitar conflictos con cambios de tema

        # Solo configurar espaciado básico
        st.markdown("""
        <style>
        /* Estilo general - ajustar padding para evitar overlap con header */
        .main .block-container {
            padding-top: 0rem !important;
            padding-bottom: 2rem !important;
            margin-top: 0rem !important;
        }

        /* Métricas - mantener tamaño consistente */
        [data-testid="stMetricValue"] {
            font-size: 28px !important;
            font-weight: 600 !important;
        }

        /* Dividers básicos */
        hr {
            margin: 2rem 0 !important;
            border: none !important;
            height: 2px !important;
        }
        </style>
        """, unsafe_allow_html=True)

    # ===================== MÉTODOS PRINCIPALES DE COORDINACIÓN =====================

    def plot_membership_functions_enhanced(self) -> None:
        """Visualización mejorada de funciones de membresía"""
        self.membership_viz.plot_enhanced()

    def plot_control_surfaces(self) -> None:
        """Módulo completo de superficies de control 3D"""
        self.surface_viz.plot_surfaces()

    def plot_rule_analysis(self, inputs: Dict[str, float]) -> None:
        """Módulo completo de análisis de reglas"""
        self.rule_viz.plot_analysis(inputs)

    def plot_plant_comparison(self) -> None:
        """Módulo de comparación de plantas"""
        self.plant_viz.plot_comparison()

    def plot_sensitivity_analysis(self, base_scenario: Dict[str, float]) -> None:
        """Análisis completo de sensibilidad"""
        self.sensitivity_viz.plot_analysis(base_scenario)



    def render_main_dashboard(self, current_inputs: Dict[str, float], outputs: Dict[str, float]) -> None:
        """Dashboard principal con todas las visualizaciones clave"""
        self.dashboard_viz.render_dashboard(current_inputs, outputs)

    # ===================== UTILIDADES COMPARTIDAS =====================

    def _get_label_color(self, label: str) -> str:
        """Retorna color según etiqueta"""
        color_map = {
            'baja': self.config.COLORS['bajo'],
            'media': self.config.COLORS['medio'],
            'alta': self.config.COLORS['alto'],
            'seca': self.config.COLORS['bajo'],
            'moderada': self.config.COLORS['medio'],
            'humeda': self.config.COLORS['alto'],
            'bajo': self.config.COLORS['bajo'],
            'medio': self.config.COLORS['medio'],
            'alto': self.config.COLORS['alto'],
            'nulo': self.config.COLORS['nulo'],
            'corto': self.config.COLORS['bajo'],
            'largo': self.config.COLORS['alto'],
        }
        return color_map.get(label, self.config.COLORS['primary'])

    def _get_activation_color(self, value: float) -> str:
        """Color según nivel de activación"""
        if value > 0.7:
            return self.config.COLORS['success']
        elif value > 0.4:
            return self.config.COLORS['warning']
        else:
            return self.config.COLORS['danger']

    def _get_default_value(self, param_name: str) -> float:
        """Valor por defecto según parámetro"""
        defaults = {
            'temperature': 25.0,
            'soil_humidity': 50.0,
            'rain_probability': 20.0,
            'air_humidity': 60.0,
            'wind_speed': 15.0
        }
        return defaults.get(param_name, 25.0)

    def _get_max_value(self, param_name: str) -> float:
        """Valor máximo según parámetro"""
        max_values = {
            'temperature': 50.0,
            'soil_humidity': 100.0,
            'rain_probability': 100.0,
            'air_humidity': 100.0,
            'wind_speed': 40.0
        }
        return max_values.get(param_name, 100.0)

    def _plot_radar_chart(self, data: Dict[str, float], height: int = 400) -> None:
        """Gráfico radar genérico"""
        labels = list(data.keys())
        values = list(data.values())

        fig = go.Figure()

        fig.add_trace(go.Scatterpolar(
            r=values + [values[0]],
            theta=labels + [labels[0]],
            fill='toself',
            fillcolor=f'rgba(46, 134, 171, 0.3)',
            line=dict(color=self.config.COLORS['primary'], width=2),
            marker=dict(size=8, color=self.config.COLORS['primary'])
        ))

        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 1],
                    showticklabels=True,
                    ticks='outside',
                    gridcolor='lightgray'
                ),
                angularaxis=dict(
                    gridcolor='lightgray'
                )
            ),
            showlegend=False,
            template=self.config.LAYOUT_TEMPLATE,
            height=height,
            font=dict(family=self.config.FONT_FAMILY)
        )

        st.plotly_chart(fig, use_container_width=True)

    def plot_gauge(self, value: float, max_val: float, title: str = "") -> None:
        """Gráfico tipo velocímetro"""
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=value,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': title, 'font': {'size': 16}},
            delta={'reference': max_val * 0.5},
            gauge={
                'axis': {'range': [0, max_val], 'tickwidth': 1},
                'bar': {'color': self.config.COLORS['primary']},
                'bgcolor': "white",
                'borderwidth': 2,
                'bordercolor': "gray",
                'steps': [
                    {'range': [0, max_val * 0.33], 'color': '#E5FFE5'},
                    {'range': [max_val * 0.33, max_val * 0.66], 'color': '#FFF4E5'},
                    {'range': [max_val * 0.66, max_val], 'color': '#FFE5E5'}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': max_val * 0.8
                }
            }
        ))

        fig.update_layout(
            height=300,
            font={'family': self.config.FONT_FAMILY}
        )

        st.plotly_chart(fig, use_container_width=True)


# ===================== FUNCIÓN PRINCIPAL =========================

def renderizar_pagina_visualizaciones() -> None:
    """Función principal para renderizar la página de visualizaciones"""

    # Header de página
    col1, col2 = st.columns([1, 10])
    with col1:
        st.write("")  # Spacer
        st.write("")  # Spacer
        st.image("assets/images/icon-chart.png", width=100)
    with col2:
        st.write("")  # Spacer
        st.write("")  # Spacer
        st.title("Visualizaciones del Sistema Difuso")
        st.write("Explore las representations gráficas del motor de inferencia difusa.")

    # ===================== CONFIGURACIÓN ACTUAL =====================

    # Inicializar valores de la calculadora o por defecto
    if 'calculadora_current' in st.session_state:
        config_data = st.session_state.calculadora_current.copy()
        current_inputs = {k: v for k, v in config_data.items() if k != 'planta'}

        # Obtener factor de ajuste de planta
        from nucleo.base_conocimientos import PLANT_KB
        planta = config_data.get('planta', 'Tomate')
        kb = PLANT_KB.get(planta, {})
        ajuste_planta = kb.get("factor_ajuste", 1.0)

        st.info("📊 Usando configuración actual de la calculadora de riego inteligente")

        # Mostrar valores actuales
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("🌡️ Temperatura", f"{current_inputs['temperature']:.1f}°C")
            st.metric("💨 Humedad Aire", f"{current_inputs['air_humidity']:.1f}%")
        with col2:
            st.metric("🌱 Humedad Suelo", f"{current_inputs['soil_humidity']:.1f}%")
            st.metric("🌧️ Prob. Lluvia", f"{current_inputs['rain_probability']:.1f}%")
        with col3:
            st.metric("🍃 Viento", f"{current_inputs['wind_speed']:.1f} km/h")
            st.metric("🌱 Planta", config_data.get('planta', 'Tomate'))
    else:
        st.warning("⚠️ No hay configuración de la calculadora. Usa primero la Calculadora de Riego Inteligente para configurar variables.")
        current_inputs = {
            'temperature': 25.0, 'soil_humidity': 50.0, 'rain_probability': 20.0,
            'air_humidity': 60.0, 'wind_speed': 15.0
        }
        ajuste_planta = 1.0

    st.markdown("---")

    # Inicializar sistema
    try:
        from ..motor_difuso import SistemaRiegoDifuso
        system = SistemaRiegoDifuso()
        visualizer = FuzzyVisualizer(system)
    except Exception as e:
        st.error(f"❌ Error inicializando sistema de riego: {e}")
        return

    # Menú de navegación con tabs
    tab_dashboard, tab_membership, tab_surfaces, tab_rules, tab_plants, tab_sensitivity = st.tabs([
        "🏠 Dashboard Principal",
        "🎛️ Funciones de Membresía",
        "🌐 Superficies 3D",
        "🔍 Análisis de Reglas",
        "🌱 Comparación de Plantas",
        "📈 Análisis de Sensibilidad"
    ])

    # Calcular outputs
    try:
        tiempo, freq, _ = system.calculate_irrigation(**current_inputs)
        outputs = {'tiempo': tiempo, 'frecuencia': freq}
    except Exception as e:
        st.error(f"Error calculando irrigación: {e}")
        outputs = {'tiempo': 0, 'frecuencia': 0}

    # Renderizar según tab seleccionado
    with tab_dashboard:
        visualizer.render_main_dashboard(current_inputs, outputs)

    with tab_membership:
        visualizer.plot_membership_functions_enhanced()

    with tab_surfaces:
        visualizer.plot_control_surfaces()

    with tab_rules:
        visualizer.plot_rule_analysis(current_inputs)

    with tab_plants:
        visualizer.plot_plant_comparison()

    with tab_sensitivity:
        visualizer.plot_sensitivity_analysis(current_inputs)


# ===================== FUNCIONES LEGACY (COMPATIBILIDAD) =========================

def plot_membership_functions(system: SistemaRiegoDifuso) -> None:
    """Función legacy - mantiene compatibilidad con código antiguo"""
    visualizer = FuzzyVisualizer(system)
    visualizer.plot_membership_functions_enhanced()


def plot_reglas_activadas(activaciones: Dict[str, float]) -> None:
    """Función legacy - mantiene compatibilidad"""
    if not activaciones:
        st.warning("No hay activaciones para mostrar")
        return

    sorted_rules = sorted(activaciones.items(), key=lambda x: x[1], reverse=True)[:15]

    fig = go.Figure(go.Bar(
        x=[r[1] for r in sorted_rules],
        y=[r[0] for r in sorted_rules],
        orientation='h',
        marker=dict(color=VisualizationConfig.COLORS['primary'])
    ))

    fig.update_layout(
        title="Activación por Regla",
        xaxis_title="Activación",
        template=VisualizationConfig.LAYOUT_TEMPLATE
    )

    st.plotly_chart(fig, use_container_width=True)


def plot_gauge(valor: float, max_val: float, title: str = "") -> None:
    """Función legacy - mantiene compatibilidad"""
    visualizer = FuzzyVisualizer()
    visualizer.plot_gauge(valor, max_val, title)


def radar_inputs(vals: Dict[str, float]) -> None:
    """Función legacy - mantiene compatibilidad"""
    visualizer = FuzzyVisualizer()
    visualizer._plot_radar_chart(vals)


def plot_surface_3d(var1: str, var2: str, output: str) -> None:
    """Función legacy - mantiene compatibilidad"""
    system = SistemaRiegoDifuso()
    visualizer = FuzzyVisualizer(system)

    # Mapear nombres antiguos a nuevos
    var_map = {
        'temperatura': 'temperature',
        'humedad_suelo': 'soil_humidity'
    }

    var1_new = var_map.get(var1, var1)
    var2_new = var_map.get(var2, var2)

    fixed_params = {
        'rain_probability': 20,
        'air_humidity': 50,
        'wind_speed': 15
    }

    X, Y, Z = visualizer.surface_viz._generate_surface_data(var1_new, var2_new, output, 30, fixed_params)

    fig = go.Figure(data=[go.Surface(z=Z, x=X, y=Y, colorscale='Viridis')])
    fig.update_layout(
        scene=dict(xaxis_title=var1, yaxis_title=var2, zaxis_title=output),
        height=500
    )
    st.plotly_chart(fig, use_container_width=True)

def plot_comparacion_plantas() -> None:
    """Función legacy - mantiene compatibilidad"""
    visualizer = FuzzyVisualizer()
    visualizer.plot_plant_comparison()
