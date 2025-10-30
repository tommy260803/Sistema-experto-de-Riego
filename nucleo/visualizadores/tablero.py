"""
Visualizaciones del Tablero Principal (Dashboard)
Especializado en el dashboard general del sistema de riego
"""

from __future__ import annotations
from typing import Dict, List, Optional
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


class RenderizadorTablero:
    """
    Renderizador del tablero principal (dashboard)
    Muestra métricas principales, análisis rápido y recomendaciones
    """

    def __init__(self, system: SistemaRiegoDifuso, config: VisualizationConfig):
        """
        Inicializa el renderizador del tablero

        Args:
            system: Instancia del sistema de riego difuso
            config: Configuración de visualización
        """
        self.system = system
        self.config = config

    def render_dashboard(self, current_inputs: Dict[str, float], outputs: Dict[str, float]) -> None:
        """Dashboard principal con todas las visualizaciones clave"""

        st.markdown("### 🏠 Dashboard del Sistema de Riego Inteligente")
        st.markdown("Vista integral del estado del sistema y recomendaciones de riego")

        # ========== SECCIÓN 1: KPIs SUPERIORES ==========
        st.markdown("### 📊 Indicadores Clave de Desempeño")

        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            st.metric(
                "⏱️ Tiempo",
                f"{outputs.get('tiempo', 0):.1f} min",
                delta=None,
                help="Tiempo de riego recomendado"
            )

        with col2:
            st.metric(
                "🔄 Frecuencia",
                f"{outputs.get('frecuencia', 0):.1f} x/día",
                delta=None,
                help="Número de riegos por día"
            )

        with col3:
            # Estimación de agua (5 L/min es un estimado)
            agua_total = outputs.get('tiempo', 0) * outputs.get('frecuencia', 0) * 5
            st.metric(
                "💧 Agua Total",
                f"{agua_total:.0f} L/día",
                delta=None,
                help="Consumo estimado de agua"
            )

        with col4:
            # Calcular eficiencia
            eficiencia = self._calculate_efficiency(current_inputs, outputs)
            delta_ef = eficiencia - 75  # 75% es baseline
            st.metric(
                "✅ Eficiencia",
                f"{eficiencia:.0f}%",
                delta=f"{delta_ef:+.0f}%",
                help="Eficiencia del sistema de riego"
            )

        with col5:
            # Estado del sistema
            estado = self._get_system_status(current_inputs)
            st.metric(
                "🎯 Estado",
                estado['label'],
                delta=None,
                help=estado['description']
            )

        # ========== SECCIÓN 2: VISUALIZACIONES PRINCIPALES ==========
        st.markdown("### 📈 Análisis Visual")

        col_left, col_center, col_right = st.columns([1, 2, 1])

        with col_left:
            st.markdown("#### 🎯 Inputs Actuales")
            self._plot_inputs_radar(current_inputs)

            # Tabla de valores
            with st.expander("📋 Ver valores"):
                input_labels = {
                    'temperature': '🌡️ Temperatura',
                    'soil_humidity': '🌱 Humedad Suelo',
                    'rain_probability': '🌧️ Prob. Lluvia',
                    'air_humidity': '💨 Humedad Aire',
                    'wind_speed': '🍃 Viento'
                }
                for key, label in input_labels.items():
                    value = current_inputs.get(key, 0)
                    st.text(f"{label}: {value:.1f}")

        with col_center:
            st.markdown("#### 🌐 Mini Superficie 3D")
            # Mini superficie 3D
            self._plot_mini_surface_3d(current_inputs)

        with col_right:
            st.markdown("#### 🔍 Reglas Activas")
            self._plot_top_rules(current_inputs)

        # ========== SECCIÓN 3: ANÁLISIS DETALLADO ==========
        st.markdown("### 🔬 Análisis Detallado")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### ⚖️ Proceso de Defuzzificación")
            self._plot_defuzzification_mini(outputs)

        with col2:
            st.markdown("#### 📊 Sensibilidad Rápida")
            self._plot_sensitivity_preview(current_inputs)

        # ========== SECCIÓN 4: RECOMENDACIONES ==========
        st.markdown("### 💡 Recomendaciones Inteligentes")
        self._show_recommendations(current_inputs, outputs)

    def _calculate_efficiency(self, inputs: Dict[str, float], outputs: Dict[str, float]) -> float:
        """Calcula eficiencia del sistema"""
        # Eficiencia base
        efficiency = 70

        # Ajustes según condiciones
        soil_hum = inputs.get('soil_humidity', 50)
        if 40 <= soil_hum <= 70:
            efficiency += 15
        elif 30 <= soil_hum <= 80:
            efficiency += 10

        rain_prob = inputs.get('rain_probability', 0)
        if rain_prob > 70:
            efficiency += 10

        temp = inputs.get('temperature', 25)
        if 18 <= temp <= 28:
            efficiency += 5

        return min(100, efficiency)

    def _get_system_status(self, inputs: Dict[str, float]) -> Dict[str, str]:
        """Determina estado del sistema"""
        soil_hum = inputs.get('soil_humidity', 50)

        if soil_hum < 30:
            return {
                'label': '🔴 Crítico',
                'description': 'Requiere riego urgente'
            }
        elif soil_hum < 45:
            return {
                'label': '🟡 Alerta',
                'description': 'Riego recomendado pronto'
            }
        elif soil_hum <= 70:
            return {
                'label': '🟢 Óptimo',
                'description': 'Condiciones ideales'
            }
        else:
            return {
                'label': '🔵 Saturado',
                'description': 'No requiere riego'
            }

    def _plot_inputs_radar(self, inputs: Dict[str, float]) -> None:
        """Radar de inputs normalizado"""
        normalized = {
            'Temp': inputs.get('temperature', 25) / 50,
            'H.Suelo': inputs.get('soil_humidity', 50) / 100,
            'Lluvia': inputs.get('rain_probability', 20) / 100,
            'H.Aire': inputs.get('air_humidity', 60) / 100,
            'Viento': inputs.get('wind_speed', 15) / 40
        }
        self._plot_radar_chart(normalized, height=300)

    def _plot_mini_surface_3d(self, inputs: Dict[str, float]) -> None:
        """Versión mini de superficie 3D"""
        # Superficie simple con resolución baja
        X, Y, Z = self._generate_surface_data(
            'temperature',
            'soil_humidity',
            'tiempo',
            20,  # Baja resolución para rapidez
            {
                'rain_probability': inputs.get('rain_probability', 20),
                'air_humidity': inputs.get('air_humidity', 60),
                'wind_speed': inputs.get('wind_speed', 15)
            }
        )

        fig = go.Figure(data=[go.Surface(
            x=X, y=Y, z=Z,
            colorscale='Viridis',
            showscale=False
        )])

        # Marcar punto actual
        current_x = inputs.get('temperature', 25)
        current_y = inputs.get('soil_humidity', 50)

        fig.add_trace(go.Scatter3d(
            x=[current_x],
            y=[current_y],
            z=[Z.max()],
            mode='markers',
            marker=dict(size=10, color='red', symbol='diamond'),
            name='Actual',
            showlegend=False
        ))

        fig.update_layout(
            scene=dict(
                xaxis_title='Temp',
                yaxis_title='H.Suelo',
                zaxis_title='Tiempo',
                camera=dict(eye=dict(x=1.5, y=1.5, z=1.2))
            ),
            height=300,
            margin=dict(l=0, r=0, t=0, b=0)
        )

        st.plotly_chart(fig, use_container_width=True)

    def _plot_top_rules(self, inputs: Dict[str, float]) -> None:
        """Top 5 reglas más activas"""
        try:
            activations = self.system.get_rule_activations(
                inputs.get('temperature', 25),
                inputs.get('soil_humidity', 50),
                inputs.get('rain_probability', 20),
                inputs.get('air_humidity', 60),
                inputs.get('wind_speed', 15)
            )

            # Top 5
            sorted_rules = sorted(activations.items(), key=lambda x: x[1], reverse=True)[:5]

            if sorted_rules:
                rules = [r[0][:25] + '...' if len(r[0]) > 25 else r[0] for r in sorted_rules]
                values = [r[1] for r in sorted_rules]

                fig = go.Figure(go.Bar(
                    y=rules,
                    x=values,
                    orientation='h',
                    marker=dict(
                        color=values,
                        colorscale='RdYlGn',
                        showscale=False
                    ),
                    text=[f'{v:.2f}' for v in values],
                    textposition='auto'
                ))

                fig.update_layout(
                    xaxis=dict(range=[0, 1]),
                    height=250,
                    margin=dict(l=0, r=0, t=20, b=0),
                    template=self.config.LAYOUT_TEMPLATE
                )

                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Sin reglas activas")
        except Exception as e:
            st.warning(f"No se pueden mostrar reglas: {e}")

    def _plot_defuzzification_mini(self, outputs: Dict[str, float]) -> None:
        """Vista mini del proceso de defuzzificación"""
        tiempo = outputs.get('tiempo', 0)
        frecuencia = outputs.get('frecuencia', 0)

        # Gauges lado a lado
        col1, col2 = st.columns(2)

        with col1:
            fig_t = go.Figure(go.Indicator(
                mode="gauge+number",
                value=tiempo,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Tiempo (min)"},
                gauge={
                    'axis': {'range': [0, 60]},
                    'bar': {'color': self.config.COLORS['primary']},
                    'steps': [
                        {'range': [0, 20], 'color': "lightgray"},
                        {'range': [20, 40], 'color': "gray"}
                    ]
                }
            ))
            fig_t.update_layout(height=200, margin=dict(l=0, r=0, t=40, b=0))
            st.plotly_chart(fig_t, use_container_width=True)

        with col2:
            fig_f = go.Figure(go.Indicator(
                mode="gauge+number",
                value=frecuencia,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Frecuencia (x/día)"},
                gauge={
                    'axis': {'range': [0, 5]},
                    'bar': {'color': self.config.COLORS['danger']},
                    'steps': [
                        {'range': [0, 2], 'color': "lightgray"},
                        {'range': [2, 4], 'color': "gray"}
                    ]
                }
            ))
            fig_f.update_layout(height=200, margin=dict(l=0, r=0, t=40, b=0))
            st.plotly_chart(fig_f, use_container_width=True)

    def _plot_sensitivity_preview(self, inputs: Dict[str, float]) -> None:
        """Vista previa de sensibilidad"""
        # Calcular impacto de cada variable
        impacts = []

        for var in ['temperature', 'soil_humidity', 'rain_probability', 'air_humidity', 'wind_speed']:
            scenario = inputs.copy()

            # Calcular en extremos
            ranges = {
                'temperature': (0, 50),
                'soil_humidity': (0, 100),
                'rain_probability': (0, 100),
                'air_humidity': (0, 100),
                'wind_speed': (0, 40)
            }

            var_range = ranges[var]

            scenario[var] = var_range[0]
            try:
                t_min, _, _ = self.system.calculate_irrigation(**scenario)
            except ValueError:
                t_min = 0

            scenario[var] = var_range[1]
            try:
                t_max, _, _ = self.system.calculate_irrigation(**scenario)
            except ValueError:
                t_max = 0

            impact = abs(t_max - t_min)
            impacts.append((var, impact))

        # Ordenar por impacto
        impacts.sort(key=lambda x: x[1], reverse=True)

        var_labels = {
            'temperature': '🌡️ Temperatura',
            'soil_humidity': '🌱 Hum. Suelo',
            'rain_probability': '🌧️ Lluvia',
            'air_humidity': '💨 Hum. Aire',
            'wind_speed': '🍃 Viento'
        }

        labels = [var_labels[v[0]] for v in impacts]
        values = [v[1] for v in impacts]

        fig = go.Figure(go.Bar(
            x=values,
            y=labels,
            orientation='h',
            marker=dict(
                color=values,
                colorscale='Reds',
                showscale=False
            ),
            text=[f'{v:.1f}' for v in values],
            textposition='auto'
        ))

        fig.update_layout(
            xaxis_title="Impacto (min)",
            height=250,
            template=self.config.LAYOUT_TEMPLATE,
            margin=dict(l=0, r=0, t=0, b=0)
        )

        st.plotly_chart(fig, use_container_width=True)

    def _show_recommendations(self, inputs: Dict[str, float], outputs: Dict[str, float]) -> None:
        """Muestra recomendaciones basadas en las condiciones"""
        recommendations = []

        soil_hum = inputs.get('soil_humidity', 50)
        rain_prob = inputs.get('rain_probability', 0)
        temp = inputs.get('temperature', 25)
        wind = inputs.get('wind_speed', 0)

        # Analizar condiciones
        if soil_hum < 30:
            recommendations.append({
                'icon': '💧',
                'title': 'Riego Urgente',
                'message': 'La humedad del suelo está críticamente baja. Se recomienda riego inmediato.',
                'priority': 'high'
            })

        if rain_prob > 70:
            recommendations.append({
                'icon': '🌧️',
                'title': 'Probabilidad Alta de Lluvia',
                'message': 'Se puede reducir o posponer el riego debido a la alta probabilidad de lluvia.',
                'priority': 'medium'
            })

        if temp > 35:
            recommendations.append({
                'icon': '🌡️',
                'title': 'Temperatura Elevada',
                'message': 'Las altas temperaturas aumentan la evapotranspiración. Considere regar en horas tempranas.',
                'priority': 'medium'
            })

        if wind > 25:
            recommendations.append({
                'icon': '🍃',
                'title': 'Viento Fuerte',
                'message': 'El viento alto puede reducir la eficiencia del riego. Ajuste los aspersores si es posible.',
                'priority': 'low'
            })

        if 40 <= soil_hum <= 70:
            recommendations.append({
                'icon': '✅',
                'title': 'Condiciones Óptimas',
                'message': 'Las condiciones actuales son ideales para el crecimiento de las plantas.',
                'priority': 'info'
            })

        # Mostrar recomendaciones
        if recommendations:
            for rec in recommendations:
                # Colores específicos que funcionan en ambos temas (texto negro sobre color claro)
                bg_color = {
                    'high': '#FFE5E5',    # Rojo claro
                    'medium': '#FFF4E5',  # Amarillo claro
                    'low': '#E8F4FD',     # Azul claro
                    'info': '#E5FFE5'     # Verde claro
                }.get(rec['priority'], '#E5FFE5')

                border_color = {
                    'high': '#E74C3C',   # Rojo fuerte
                    'medium': '#F39C12', # Naranja
                    'low': '#3498DB',    # Azul
                    'info': '#27AE60'    # Verde fuerte
                }.get(rec['priority'], '#27AE60')

                text_color = {
                    'high': '#2C3E50',   # Texto oscuro sobre rojo claro
                    'medium': '#2C3E50', # Texto oscuro sobre amarillo claro
                    'low': '#2C3E50',   # Texto oscuro sobre azul claro
                    'info': '#2C3E50'   # Texto oscuro sobre verde claro
                }.get(rec['priority'], '#2C3E50')

                st.markdown(f"""
                <div style="background-color: {bg_color};
                            padding: 15px;
                            border-radius: 8px;
                            margin: 10px 0;
                            border-left: 4px solid {border_color};
                            color: {text_color} !important;
                            font-weight: normal;
                            line-height: 1.4;">
                    <h4 style="margin: 0 0 8px 0; color: {text_color} !important; font-weight: 600; font-size: 16px;">{rec['icon']} {rec['title']}</h4>
                    <p style="margin: 0; color: {text_color} !important; font-weight: normal; font-size: 14px;">{rec['message']}</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.success("✅ No hay recomendaciones especiales en este momento.")

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

    def _generate_surface_data(self, var1: str, var2: str, output: str, resolution: int, fixed_params: Dict[str, float]):
        """Genera los datos de la superficie 3D"""

        # Rangos según variable
        ranges = {
            'temperature': (0, 50),
            'soil_humidity': (0, 100),
            'rain_probability': (0, 100),
            'air_humidity': (0, 100),
            'wind_speed': (0, 40)
        }

        x_range = ranges[var1]
        y_range = ranges[var2]

        X = np.linspace(x_range[0], x_range[1], resolution)
        Y = np.linspace(y_range[0], y_range[1], resolution)
        X, Y = np.meshgrid(X, Y)

        Z = np.zeros_like(X)

        # Calcular superficie
        for i in range(resolution):
            for j in range(resolution):
                # Construir inputs
                inputs = fixed_params.copy()
                inputs[var1] = float(X[i, j])
                inputs[var2] = float(Y[i, j])

                # Calcular irrigación
                try:
                    tiempo, freq, _ = self.system.calculate_irrigation(**inputs)
                    Z[i, j] = tiempo if output == 'tiempo' else freq
                except Exception as e:
                    Z[i, j] = 0.0

        return X, Y, Z
