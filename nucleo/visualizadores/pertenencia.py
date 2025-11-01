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
    TIME_UNIVERSE,
    FREQ_UNIVERSE,
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
            ["Individual Interactivo", "Grid Completo", "Salidas del Sistema"],
            horizontal=True,
            key="membership_view_mode"
        )

        if view_mode == "Individual Interactivo":
            self._plot_interactive()
        elif view_mode == "Grid Completo":
            self._plot_grid()
        elif view_mode == "Salidas del Sistema":
            self._plot_output_functions()

    def _plot_interactive(self) -> None:
        """Modo interactivo con simulación en vivo"""

        # Obtener valores actuales de la calculadora si existen
        calc_current = st.session_state.get('calculadora_current', {})

        variables_info = {
            "Temperatura (°C)": {
                "universe": TEMP_UNIVERSE,
                "var": self.system.temperatura,
                "labels": ["baja", "media", "alta"],
                "range": (0, 50),
                "default": calc_current.get('temperature', 25.0),
                "icon": "🌡️",
                "description": "Temperatura ambiente que afecta la evapotranspiración"
            },
            "Humedad Suelo (%)": {
                "universe": SOIL_UNIVERSE,
                "var": self.system.h_suelo,
                "labels": ["seca", "moderada", "humeda"],
                "range": (0, 100),
                "default": calc_current.get('soil_humidity', 50.0),
                "icon": "🌱",
                "description": "Nivel de humedad en el suelo medido por sensores"
            },
            "Prob. Lluvia (%)": {
                "universe": RAIN_UNIVERSE,
                "var": self.system.lluvia,
                "labels": ["baja", "media", "alta"],
                "range": (0, 100),
                "default": calc_current.get('rain_probability', 20.0),
                "icon": "🌧️",
                "description": "Probabilidad de precipitación en las próximas horas"
            },
            "Humedad Aire (%)": {
                "universe": AIRH_UNIVERSE,
                "var": self.system.h_aire,
                "labels": ["baja", "media", "alta"],
                "range": (0, 100),
                "default": calc_current.get('air_humidity', 60.0),
                "icon": "💨",
                "description": "Humedad relativa del aire ambiente"
            },
            "Velocidad Viento (km/h)": {
                "universe": WIND_UNIVERSE,
                "var": self.system.viento,
                "labels": ["bajo", "medio", "alto"],
                "range": (0, 50),
                "default": calc_current.get('wind_speed', 15.0),
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
                        font=dict(size=12, family='Arial', color='black')
                    ),
                    font=dict(family='Arial', size=12, color='black'),
                    xaxis=dict(
                        gridcolor='#EAEAEA',
                        linecolor='#2D3436',
                        linewidth=2,
                        title_font=dict(color='black'),
                        tickfont=dict(color='black')
                    ),
                    yaxis=dict(
                        gridcolor='#EAEAEA',
                        linecolor='#2D3436',
                        linewidth=2,
                        range=[0, 1.1],
                        title_font=dict(color='black'),
                        tickfont=dict(color='black')
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
                            bg_color, text_color, status = '#F8D7DA', "#1D1D1D", "⬇️ Bajo"

                        st.markdown(f"""
                        <style>
                        .custom-box span {{
                            color: black !important;
                        }}
                        </style>
                        <div class="custom-box" style="background-color: {bg_color}; padding: 10px; border-radius: 5px; border-left: 4px solid {text_color};">
                            <strong style="color: {text_color};">{label.capitalize()}</strong><br>
                            <span style="color: black !important; font-weight: bold; font-size: 18px;">{value:.3f}</span><br>
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
            ("Velocidad Viento (km/h)", WIND_UNIVERSE, self.system.viento, ["bajo", "medio", "alto"], "🍃"),
        ]

        safe_colors = ['#FF6B6B', '#FFD93D', '#6BCF7F']

        # Primera fila: 3 columnas
        cols = st.columns(3)
        for j in range(3):
            if j >= len(variables):
                break

            title, universe, var, labels, icon = variables[j]

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
                        title=dict(text=f"{icon} {title}", font=dict(color='black', size=10, family='Arial')),
                        xaxis_title="Valor",
                        yaxis_title="μ",
                        template='plotly_white',
                        height=250,
                        showlegend=True,
                        plot_bgcolor='white',
                        paper_bgcolor='white',
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=-0.3,
                            xanchor="center",
                            x=0.5,
                            font=dict(color='black', size=8)
                        ),
                        margin=dict(l=30, r=30, t=50, b=50),
                        font=dict(size=9, family='Arial', color='black'),
                        xaxis=dict(
                            title_font=dict(color='black'),
                            tickfont=dict(color='black')
                        ),
                        yaxis=dict(
                            title_font=dict(color='black'),
                            tickfont=dict(color='black')
                        )
                    )

                    st.plotly_chart(fig, use_container_width=True)

            except Exception as e:
                with cols[j]:
                    st.error(f"Error en {title}: {str(e)[:50]}...")

        # Segunda fila: 2 columnas (variables restantes)
        if len(variables) > 3:
            cols = st.columns(2)
            for j in range(2):
                idx = j + 3
                if idx >= len(variables):
                    break

                title, universe, var, labels, icon = variables[idx]

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
                            title=dict(text=f"{icon} {title}", font=dict(color='black', size=10, family='Arial')),
                            xaxis_title="Valor",
                            yaxis_title="μ",
                            template='plotly_white',
                            height=250,
                            showlegend=True,
                            plot_bgcolor='white',
                            paper_bgcolor='white',
                            legend=dict(
                                orientation="h",
                                yanchor="bottom",
                                y=-0.3,
                                xanchor="center",
                                x=0.5,
                                font=dict(color='black', size=8)
                            ),
                            margin=dict(l=30, r=30, t=50, b=50),
                            font=dict(size=9, family='Arial', color='black'),
                            xaxis=dict(
                                title_font=dict(color='black'),
                                tickfont=dict(color='black')
                            ),
                            yaxis=dict(
                                title_font=dict(color='black'),
                                tickfont=dict(color='black')
                            )
                        )

                        st.plotly_chart(fig, use_container_width=True)

                except Exception as e:
                    with cols[j]:
                        st.error(f"Error en {title}: {str(e)[:50]}...")

    def _plot_output_functions(self) -> None:
        """Visualización de las funciones de membresía de las salidas del sistema"""

        st.markdown("#### 📈 Funciones de Membresía - Salidas del Sistema")

        # Primera fila: Tiempo de riego
        st.markdown("##### ⏱️ Tiempo de Riego (0-60 minutos)")
        fig_time = go.Figure()

        colors_time = ['#FF6B6B', '#FFD93D', '#6BCF7F', '#FF8C42']  # nulo, corto, medio, largo
        labels_time = ['nulo', 'corto', 'medio', 'largo']

        for i, label in enumerate(labels_time):
            color = colors_time[i % len(colors_time)]
            fig_time.add_trace(go.Scatter(
                x=TIME_UNIVERSE,
                y=self.system.tiempo[label].mf,
                name=label.capitalize(),
                mode='lines',
                line=dict(width=3, color=color),
                hovertemplate=f'<b>{label.capitalize()}</b><br>Tiempo: %{{x:.1f}} min<br>Membresía: %{{y:.3f}}<extra></extra>'
            ))

        fig_time.update_layout(
            title=dict(text="Funciones de Membresía del Tiempo de Riego", font=dict(color='black', size=14, family='Arial')),
            xaxis_title="Tiempo (minutos)",
            yaxis_title="Grado de Membresía (μ)",
            template='plotly_white',
            height=350,
            showlegend=True,
            plot_bgcolor='white',
            paper_bgcolor='white',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.2,
                xanchor="center",
                x=0.5,
                font=dict(color='black')
            ),
            font=dict(size=10, family='Arial', color='black'),
            xaxis=dict(
                title_font=dict(color='black'),
                tickfont=dict(color='black')
            ),
            yaxis=dict(
                title_font=dict(color='black'),
                tickfont=dict(color='black')
            )
        )

        st.plotly_chart(fig_time, use_container_width=True)

        # Segunda fila: Frecuencia de riego
        st.markdown("##### 🔄 Frecuencia de Riego (0.5-4 veces/día)")
        fig_freq = go.Figure()

        colors_freq = ['#FF6B6B', '#FFD93D', '#6BCF7F']  # baja, media, alta
        labels_freq = ['baja', 'media', 'alta']

        for i, label in enumerate(labels_freq):
            color = colors_freq[i % len(colors_freq)]
            fig_freq.add_trace(go.Scatter(
                x=FREQ_UNIVERSE,
                y=self.system.frecuencia[label].mf,
                name=label.capitalize(),
                mode='lines',
                line=dict(width=3, color=color),
                hovertemplate=f'<b>{label.capitalize()}</b><br>Frecuencia: %{{x:.1f}} riegos/día<br>Membresía: %{{y:.3f}}<extra></extra>'
            ))

        fig_freq.update_layout(
            title=dict(text="Funciones de Membresía de la Frecuencia de Riego", font=dict(color='black', size=14, family='Arial')),
            xaxis_title="Frecuencia (riegos por día)",
            yaxis_title="Grado de Membresía (μ)",
            template='plotly_white',
            height=350,
            showlegend=True,
            plot_bgcolor='white',
            paper_bgcolor='white',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.2,
                xanchor="center",
                x=0.5,
                font=dict(color='black')
            ),
            font=dict(size=10, family='Arial', color='black'),
            xaxis=dict(
                title_font=dict(color='black'),
                tickfont=dict(color='black')
            ),
            yaxis=dict(
                title_font=dict(color='black'),
                tickfont=dict(color='black')
            )
        )

        st.plotly_chart(fig_freq, use_container_width=True)

        # Tabla de resumen
        st.markdown("**Definiciones de los conjuntos difusos de salida:**")
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("""
            **Tiempo de Riego:**
            - **Nulo**: 0-5 minutos (prácticamente sin riego)
            - **Corto**: 3-20 minutos (riego ligero)
            - **Medio**: 15-40 minutos (riego moderado)
            - **Largo**: 35-60 minutos (riego intensivo)
            """)

        with col2:
            st.markdown("""
            **Frecuencia de Riego:**
            - **Baja**: 0.5-1.5 riegos/día (riego espaciado)
            - **Media**: 1.0-2.5 riegos/día (riego regular)
            - **Alta**: 2.0-4.0 riegos/día (riego frecuente)
            """)

    def _get_label_color(self, label: str) -> str:
        """Retorna color según etiqueta con fallback seguro"""
        safe_colors = {
            'baja': '#FF6B6B', 'seca': '#FF6B6B', 'bajo': '#FF6B6B',
            'media': '#FFD93D', 'moderada': '#FFD93D', 'medio': '#FFD93D',
            'alta': '#6BCF7F', 'humeda': '#6BCF7F', 'alto': '#6BCF7F',
        }
        return safe_colors.get(label, '#6C5CE7')
