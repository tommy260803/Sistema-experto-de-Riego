"""
Visualizaciones de Análisis de Reglas
Especializado en visualizaciones de reglas de inferencia difusa
"""

from __future__ import annotations
from typing import Dict, List, Optional
import numpy as np

try:
    import streamlit as st
    import plotly.graph_objects as go
    import plotly.express as px
except ImportError as e:
    raise ImportError(f"Missing required packages: {e}")

from .configuracion import VisualizationConfig
from ..motor_difuso import SistemaRiegoDifuso


class VisualizadorReglas:
    """
    Visualizador especializado en análisis de reglas de inferencia
    Maneja todas las visualizaciones relacionadas con reglas difusas
    """

    def __init__(self, system: SistemaRiegoDifuso, config: VisualizationConfig):
        """
        Inicializa el visualizador de reglas

        Args:
            system: Instancia del sistema de riego difuso
            config: Configuración de visualización
        """
        self.system = system
        self.config = config

    def plot_analysis(self, inputs: Dict[str, float]) -> None:
        """Módulo completo de análisis de reglas"""

        st.markdown("### 🔍 Análisis de Reglas Fuzzy")
        st.markdown("Visualización de las reglas activadas y su contribución al resultado")

        # Obtener activaciones
        try:
            activations = self.system.get_rule_activations(
                inputs.get('temperature', 25),
                inputs.get('soil_humidity', 50),
                inputs.get('rain_probability', 20),
                inputs.get('air_humidity', 60),
                inputs.get('wind_speed', 15)
            )
        except Exception as e:
            st.error(f"Error al obtener activaciones: {e}")
            return

        if not activations:
            st.warning("⚠️ No se pudieron obtener las activaciones de las reglas")
            return

        # Filtrar reglas significativas
        significant = {k: v for k, v in activations.items() if v > 0.01}

        if not significant:
            st.info("ℹ️ Ninguna regla activada significativamente con estos valores")
            return

        # Tabs para diferentes vistas
        tab1, tab2, tab3 = st.tabs(["📊 Ranking", "🎯 Detalle", "🔥 Mapa de Calor"])

        with tab1:
            self._plot_rule_ranking(significant)

        with tab2:
            self._plot_rule_details(significant, inputs)

        with tab3:
            self._plot_rule_heatmap(activations)

    def _plot_rule_ranking(self, activations: Dict[str, float]) -> None:
        """Ranking de reglas por activación"""

        sorted_rules = sorted(activations.items(), key=lambda x: x[1], reverse=True)
        top_n = min(15, len(sorted_rules))

        col1, col2 = st.columns([3, 1])

        with col1:
            # Gráfico de barras horizontal
            fig = go.Figure()

            rules = [r[0] for r in sorted_rules[:top_n]]
            values = [r[1] for r in sorted_rules[:top_n]]

            # Colores según intensidad
            colors = [self._get_activation_color(v) for v in values]

            fig.add_trace(go.Bar(
                y=rules,
                x=values,
                orientation='h',
                marker=dict(
                    color=colors,
                    line=dict(color='white', width=1)
                ),
                text=[f'{v:.3f}' for v in values],
                textposition='auto',
                textfont=dict(color='white', size=11, family=self.config.FONT_FAMILY),
                hovertemplate='<b>%{y}</b><br>Activación: %{x:.4f}<extra></extra>'
            ))

            fig.update_layout(
                title=f"Top {top_n} Reglas Más Activas",
                xaxis_title="Grado de Activación",
                yaxis_title="",
                template=self.config.LAYOUT_TEMPLATE,
                height=max(400, top_n * 30),
                xaxis=dict(range=[0, 1]),
                font=dict(family=self.config.FONT_FAMILY)
            )

            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown("#### 📈 Estadísticas")
            st.metric("Total Reglas Activas", len(activations))
            st.metric("Regla Dominante", sorted_rules[0][0][:20] + "...")
            st.metric("Activación Máx", f"{sorted_rules[0][1]:.3f}")
            st.metric("Activación Prom", f"{np.mean(list(activations.values())):.3f}")

            # Distribución de activaciones
            st.markdown("#### 📊 Distribución")
            ranges = {
                "Alta (>0.7)": len([v for v in activations.values() if v > 0.7]),
                "Media (0.3-0.7)": len([v for v in activations.values() if 0.3 <= v <= 0.7]),
                "Baja (<0.3)": len([v for v in activations.values() if v < 0.3])
            }

            for label, count in ranges.items():
                st.metric(label, count)

    def _plot_rule_details(self, activations: Dict[str, float], inputs: Dict) -> None:
        """Detalles de reglas individuales"""

        sorted_rules = sorted(activations.items(), key=lambda x: x[1], reverse=True)

        # Selector de regla
        selected_rule_name = st.selectbox(
            "Seleccionar regla para analizar",
            [r[0] for r in sorted_rules[:20]],
            format_func=lambda x: f"{x} (μ={activations[x]:.3f})"
        )

        activation_value = activations[selected_rule_name]

        # Card de la regla
        bg_color = '#FFE5E5' if activation_value > 0.7 else '#FFF4E5' if activation_value > 0.4 else '#E5FFE5'
        border_color = '#E74C3C' if activation_value > 0.7 else '#F39C12' if activation_value > 0.4 else '#06A77D'

        st.markdown(f"""
        <div style="background-color: {bg_color};
                    padding: 15px;
                    border-radius: 8px;
                    margin: 10px 0;
                    border-left: 4px solid {border_color};">
            <h4 style="margin: 0 0 8px 0;">🎯 {selected_rule_name}</h4>
            <p><strong>Grado de Activación:</strong> {activation_value:.4f}</p>
        </div>
        """, unsafe_allow_html=True)

        # Visualización de contribución
        col1, col2 = st.columns(2)

        with col1:
            # Gauge de activación
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=activation_value,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Nivel de Activación", 'font': {'size': 16}},
                delta={'reference': 0.5},
                gauge={
                    'axis': {'range': [None, 1], 'tickwidth': 1},
                    'bar': {'color': self._get_activation_color(activation_value)},
                    'bgcolor': "white",
                    'borderwidth': 2,
                    'bordercolor': "gray",
                    'steps': [
                        {'range': [0, 0.3], 'color': '#FFE5E5'},
                        {'range': [0.3, 0.7], 'color': '#FFF4E5'},
                        {'range': [0.7, 1], 'color': '#E5FFE5'}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 0.9
                    }
                }
            ))

            fig_gauge.update_layout(
                height=300,
                font={'family': self.config.FONT_FAMILY}
            )

            st.plotly_chart(fig_gauge, use_container_width=True)

        with col2:
            # Radar de inputs que activan esta regla
            st.markdown("##### 🎯 Inputs Contribuyentes")

            # Normalizar inputs para radar
            normalized_inputs = {
                'Temp': inputs.get('temperature', 25) / 50,
                'H.Suelo': inputs.get('soil_humidity', 50) / 100,
                'Lluvia': inputs.get('rain_probability', 20) / 100,
                'H.Aire': inputs.get('air_humidity', 60) / 100,
                'Viento': inputs.get('wind_speed', 15) / 40
            }

            self._plot_radar_chart(normalized_inputs, height=300)

    def _plot_rule_heatmap(self, activations: Dict[str, float]) -> None:
        """Mapa de calor de todas las reglas"""

        st.markdown("#### 🔥 Mapa de Calor de Activaciones")

        # Preparar datos para heatmap (agrupar por categorías)
        rules_list = list(activations.items())

        # Crear matriz simulada
        n_rows = min(10, len(rules_list))
        n_cols = max(1, len(rules_list) // n_rows)

        matrix_data = []
        rule_names = []

        for i in range(n_rows):
            row = []
            for j in range(n_cols):
                idx = i * n_cols + j
                if idx < len(rules_list):
                    row.append(rules_list[idx][1])
                    if j == 0:
                        rule_names.append(rules_list[idx][0][:30])
                else:
                    row.append(0)
            matrix_data.append(row)

        # Crear heatmap
        fig = go.Figure(data=go.Heatmap(
            z=matrix_data,
            y=rule_names,
            colorscale='RdYlGn',
            colorbar=dict(title="Activación"),
            hovertemplate='Regla: %{y}<br>Activación: %{z:.3f}<extra></extra>'
        ))

        fig.update_layout(
            title="Intensidad de Activación por Regla",
            template=self.config.LAYOUT_TEMPLATE,
            height=400,
            xaxis_title="Grupo de Reglas",
            yaxis_title="Reglas",
            font=dict(family=self.config.FONT_FAMILY)
        )

        st.plotly_chart(fig, use_container_width=True)

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

    def _get_activation_color(self, value: float) -> str:
        """Color según nivel de activación"""
        if value > 0.7:
            return self.config.COLORS['success']
        elif value > 0.4:
            return self.config.COLORS['warning']
        else:
            return self.config.COLORS['danger']
