"""
Visualizaciones de Funciones de Membresía
Especializado en gráficos de funciones de pertenencia fuzzy
"""

from __future__ import annotations
from typing import Dict, List, Optional
import numpy as np

try:
    import streamlit as st
    import plotly.graph_objects as go
except ImportError as e:
    raise ImportError(f"Missing required packages: {e}")

from .configuracion import VisualizationConfig
from ..motor_difuso import (
    TEMP_UNIVERSE,
    SOIL_UNIVERSE,
    RAIN_UNIVERSE,
    AIRH_UNIVERSE,
    WIND_UNIVERSE,
    SistemaRiegoDifuso,
)


class VisualizadorPertenencia:

    def __init__(self, system: SistemaRiegoDifuso, config: VisualizationConfig):
        self.system = system
        self.config = config

    def plot_enhanced(self) -> None:
        """Visualización mejorada de funciones de membresía"""

        st.markdown("### 🎛️ Funciones de Membresía del Sistema")
        st.markdown("Visualización de los conjuntos difusos que definen las variables lingüísticas")

        view_mode = st.radio(
            "Modo de visualización",
            ["Individual Interactivo", "Grid Completo"],
            horizontal=True,
            key="membership_view_mode"
        )

        if view_mode == "Individual Interactivo":
            self._plot_interactive()
        elif view_mode == "Grid Completo":
            self._plot_grid()

    def _plot_interactive(self) -> None:
        """Modo interactivo con simulación en vivo"""

        variables_info = {
            "Temperatura (°C)": {
                "universe": TEMP_UNIVERSE,
                "var": self.system.temperatura,
                "labels": ["baja", "media", "alta"],
                "range": (0, 50),
                "default": 25,
                "icon": "🌡️",
                "description": "Temperatura ambiente que afecta la evapotranspiración"
            },
            "Humedad Suelo (%)": {
                "universe": SOIL_UNIVERSE,
                "var": self.system.h_suelo,
                "labels": ["seca", "moderada", "humeda"],
                "range": (0, 100),
                "default": 50,
                "icon": "🌱",
                "description": "Nivel de humedad en el suelo medido por sensores"
            },
            "Prob. Lluvia (%)": {
                "universe": RAIN_UNIVERSE,
                "var": self.system.lluvia,
                "labels": ["baja", "media", "alta"],
                "range": (0, 100),
                "default": 20,
                "icon": "🌧️",
                "description": "Probabilidad de precipitación en las próximas horas"
            },
            "Humedad Aire (%)": {
                "universe": AIRH_UNIVERSE,
                "var": self.system.h_aire,
                "labels": ["baja", "media", "alta"],
                "range": (0, 100),
                "default": 60,
                "icon": "💨",
                "description": "Humedad relativa del aire ambiente"
            },
            "Velocidad Viento (km/h)": {
                "universe": WIND_UNIVERSE,
                "var": self.system.viento,
                "labels": ["bajo", "medio", "alto"],
                "range": (0, 50),
                "default": 15,
                "icon": "🍃",
                "description": "Velocidad del viento que afecta la evapotranspiración"
            },
        }

        col_selector, col_graph = st.columns([1, 3])

        with col_selector:
            st.markdown("#### Seleccionar Variable")
            selected_var = st.selectbox(
                "Variable",
                list(variables_info.keys()),
                label_visibility="collapsed",
                key="variable_selector"
            )

            info = variables_info[selected_var]
            st.info(f"{info['icon']} {info['description']}")

            test_value = st.slider(
                "Valor de prueba",
                min_value=float(info['range'][0]),
                max_value=float(info['range'][1]),
                value=float(info['default']),
                step=0.5,
                key="test_value_slider"
            )

        with col_graph:
            try:
                fig = go.Figure()

                universe = info['universe']
                var = info['var']
                labels = info['labels']

                safe_colors = {
                    'baja': '#FF6B6B', 'seca': '#FF6B6B', 'bajo': '#FF6B6B',
                    'media': '#FFD93D', 'moderada': '#FFD93D', 'medio': '#FFD93D',
                    'alta': '#6BCF7F', 'humeda': '#6BCF7F', 'alto': '#6BCF7F',
                }

                fill_colors = {
                    'baja': 'rgba(255, 107, 107, 0.2)', 'seca': 'rgba(255, 107, 107, 0.2)', 'bajo': 'rgba(255, 107, 107, 0.2)',
                    'media': 'rgba(255, 217, 61, 0.2)', 'moderada': 'rgba(255, 217, 61, 0.2)', 'medio': 'rgba(255, 217, 61, 0.2)',
                    'alta': 'rgba(107, 207, 127, 0.2)', 'humeda': 'rgba(107, 207, 127, 0.2)', 'alto': 'rgba(107, 207, 127, 0.2)',
                }

                for i, label in enumerate(labels):
                    color = safe_colors.get(label, '#6C5CE7')
                    fillcolor = fill_colors.get(label, 'rgba(108, 92, 231, 0.2)')

                    try:
                        fig.add_trace(go.Scatter(
                            x=universe,
                            y=var[label].mf,
                            name=label.capitalize(),
                            mode='lines',
                            line=dict(width=4, color=color),
                            fill='tonexty' if i == 0 else None,
                            fillcolor=fillcolor,
                            hovertemplate=f'<b>{label.capitalize()}</b><br>Valor: %{{x:.1f}}<br>Membresía: %{{y:.3f}}<extra></extra>'
                        ))
                    except Exception as e:
                        st.error(f"Error graficando '{label}': {e}")
                        continue

                fig.add_vline(
                    x=test_value,
                    line_dash="dash",
                    line_color='#E17055',
                    line_width=3,
                    annotation_text=f"Valor: {test_value:.1f}",
                    annotation_position="top",
                    annotation_font=dict(color='#E17055', size=14, family='Arial Black')
                )

                memberships = {}
                for label in labels:
                    try:
                        membership_value = np.interp(test_value, universe, var[label].mf)
                        memberships[label] = membership_value
                    except Exception as e:
                        memberships[label] = 0.0

                fig.update_layout(
                    title=dict(
                        text=f"{info['icon']} {selected_var}",
                        font=dict(size=20, family='Arial Black', color='#2D3436')
                    ),
                    xaxis_title="Valor",
                    yaxis_title="Grado de Membresía (μ)",
                    hovermode='x unified',
                    template='plotly_white',
                    height=500,
                    plot_bgcolor='white',
                    paper_bgcolor='white',
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1,
                        font=dict(size=12, family='Arial')
                    ),
                    font=dict(family='Arial', size=12),
                    xaxis=dict(
                        gridcolor='#EAEAEA',
                        linecolor='#2D3436',
                        linewidth=2
                    ),
                    yaxis=dict(
                        gridcolor='#EAEAEA',
                        linecolor='#2D3436',
                        linewidth=2,
                        range=[0, 1.1]
                    )
                )

                st.plotly_chart(fig, use_container_width=True)

                st.markdown("##### 📊 Valores de Membresía")
                cols = st.columns(len(labels))
                for idx, (label, value) in enumerate(memberships.items()):
                    with cols[idx]:
                        if value >= 0.7:
                            bg_color, text_color, status = '#D5F4E6', '#00B894', "🔝 Alto"
                        elif value >= 0.4:
                            bg_color, text_color, status = '#FFF3CD', '#856404', "~ Medio"
                        else:
                            bg_color, text_color, status = '#F8D7DA', '#721C24', "⬇️ Bajo"

                        st.markdown(f"""
                        <div style="background-color: {bg_color}; padding: 10px; border-radius: 5px; border-left: 4px solid {text_color};">
                            <strong style="color: {text_color};">{label.capitalize()}</strong><br>
                            <span style="font-size: 18px; font-weight: bold; color: {text_color};">{value:.3f}</span><br>
                            <small style="color: {text_color};">{status}</small>
                        </div>
                        """, unsafe_allow_html=True)

            except Exception as e:
                st.error(f"❌ Error al generar la gráfica: {str(e)}")
                st.info("💡 Intenta seleccionar una variable diferente o refrescar la página")

    def _plot_grid(self) -> None:
        """Grid completo de todas las funciones de membresía"""

        st.markdown("#### 📐 Vista Completa del Sistema")

        variables = [
            ("Temperatura (°C)", TEMP_UNIVERSE, self.system.temperatura, ["baja", "media", "alta"], "🌡️"),
            ("Humedad Suelo (%)", SOIL_UNIVERSE, self.system.h_suelo, ["seca", "moderada", "humeda"], "🌱"),
            ("Prob. Lluvia (%)", RAIN_UNIVERSE, self.system.lluvia, ["baja", "media", "alta"], "🌧️"),
            ("Humedad Aire (%)", AIRH_UNIVERSE, self.system.h_aire, ["baja", "media", "alta"], "💨"),
        ]

        safe_colors = ['#FF6B6B', '#FFD93D', '#6BCF7F']

        for i in range(0, len(variables), 2):
            cols = st.columns(2)
            for j in range(2):
                if i + j >= len(variables):
                    break

                title, universe, var, labels, icon = variables[i + j]

                try:
                    with cols[j]:
                        fig = go.Figure()

                        for k, label in enumerate(labels):
                            color = safe_colors[k % len(safe_colors)]
                            fig.add_trace(go.Scatter(
                                x=universe,
                                y=var[label].mf,
                                name=label.capitalize(),
                                mode='lines',
                                line=dict(width=3, color=color),
                                hovertemplate=f'{label}: %{{y:.2f}}<extra></extra>'
                            ))

                        fig.update_layout(
                            title=f"{icon} {title}",
                            xaxis_title="Valor",
                            yaxis_title="μ",
                            template='plotly_white',
                            height=300,
                            showlegend=True,
                            plot_bgcolor='white',
                            paper_bgcolor='white',
                            legend=dict(
                                orientation="h",
                                yanchor="bottom",
                                y=-0.2,
                                xanchor="center",
                                x=0.5
                            ),
                            margin=dict(l=40, r=40, t=60, b=60),
                            font=dict(size=10, family='Arial')
                        )

                        st.plotly_chart(fig, use_container_width=True)

                except Exception as e:
                    with cols[j]:
                        st.error(f"Error en {title}: {str(e)[:50]}...")

    def _get_label_color(self, label: str) -> str:
        """Retorna color según etiqueta con fallback seguro"""
        safe_colors = {
            'baja': '#FF6B6B', 'seca': '#FF6B6B', 'bajo': '#FF6B6B',
            'media': '#FFD93D', 'moderada': '#FFD93D', 'medio': '#FFD93D',
            'alta': '#6BCF7F', 'humeda': '#6BCF7F', 'alto': '#6BCF7F',
        }
        return safe_colors.get(label, '#6C5CE7')
