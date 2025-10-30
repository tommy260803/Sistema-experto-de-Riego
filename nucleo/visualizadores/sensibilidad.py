"""
Visualizaciones de Análisis de Sensibilidad
Especializado en análisis de impacto de variables
"""

from __future__ import annotations
from typing import Dict, List, Optional
import numpy as np
from scipy import stats

try:
    import streamlit as st
    import plotly.graph_objects as go
    import plotly.express as px
except ImportError as e:
    raise ImportError(f"Missing required packages: {e}")

from .configuracion import VisualizationConfig
from ..motor_difuso import SistemaRiegoDifuso


class VisualizadorSensibilidad:
    """
    Visualizador especializado en análisis de sensibilidad
    Evalúa cómo cambian las salidas ante variaciones en las entradas
    """

    def __init__(self, system: SistemaRiegoDifuso, config: VisualizationConfig):
        """
        Inicializa el visualizador de sensibilidad

        Args:
            system: Instancia del sistema de riego difuso
            config: Configuración de visualización
        """
        self.system = system
        self.config = config

    def plot_analysis(self, base_scenario: Dict[str, float]) -> None:
        """Análisis completo de sensibilidad"""

        st.markdown("### 📈 Análisis de Sensibilidad")
        st.markdown("Evalúa cómo cambian las salidas al variar cada variable de entrada")

        # Configuración
        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            var_to_analyze = st.selectbox(
                "Variable a analizar",
                ["temperature", "soil_humidity", "rain_probability", "air_humidity", "wind_speed"],
                format_func=lambda x: {
                    "temperature": "🌡️ Temperatura",
                    "soil_humidity": "🌱 Humedad Suelo",
                    "rain_probability": "🌧️ Prob. Lluvia",
                    "air_humidity": "💨 Humedad Aire",
                    "wind_speed": "🍃 Viento"
                }[x]
            )

        with col2:
            num_points = st.slider("Puntos de análisis", 20, 100, 50)

        with col3:
            show_base = st.checkbox("Mostrar valor base", value=True)

        # Rango de la variable
        ranges = {
            'temperature': (0, 50),
            'soil_humidity': (0, 100),
            'rain_probability': (0, 100),
            'air_humidity': (0, 100),
            'wind_speed': (0, 40)
        }

        var_range = ranges[var_to_analyze]
        values = np.linspace(var_range[0], var_range[1], num_points)

        # Calcular respuestas
        tiempos = []
        frecuencias = []

        with st.spinner("🔄 Calculando sensibilidad..."):
            for val in values:
                scenario = base_scenario.copy()
                scenario[var_to_analyze] = val
                try:
                    t, f, _ = self.system.calculate_irrigation(**scenario)
                    tiempos.append(t)
                    frecuencias.append(f)
                except:
                    tiempos.append(0)
                    frecuencias.append(0)

        # Graficar
        from plotly.subplots import make_subplots
        fig = make_subplots(specs=[[{"secondary_y": True}]])

        # Tiempo
        fig.add_trace(
            go.Scatter(
                x=values,
                y=tiempos,
                name="Tiempo (min)",
                line=dict(color=self.config.COLORS['primary'], width=3),
                mode='lines',
                fill='tozeroy',
                fillcolor=f'rgba(46, 134, 171, 0.1)'
            ),
            secondary_y=False
        )

        # Frecuencia
        fig.add_trace(
            go.Scatter(
                x=values,
                y=frecuencias,
                name="Frecuencia (x/día)",
                line=dict(color=self.config.COLORS['danger'], width=3),
                mode='lines',
                fill='tozeroy',
                fillcolor=f'rgba(199, 62, 29, 0.1)'
            ),
            secondary_y=True
        )

        # Valor base
        if show_base:
            base_val = base_scenario[var_to_analyze]
            fig.add_vline(
                x=base_val,
                line_dash="dash",
                line_color=self.config.COLORS['success'],
                line_width=2,
                annotation_text=f"Base: {base_val:.1f}",
                annotation_position="top"
            )

        # Layout
        var_names = {
            'temperature': 'Temperatura (°C)',
            'soil_humidity': 'Humedad Suelo (%)',
            'rain_probability': 'Probabilidad Lluvia (%)',
            'air_humidity': 'Humedad Aire (%)',
            'wind_speed': 'Viento (km/h)'
        }

        fig.update_xaxes(title_text=var_names[var_to_analyze])
        fig.update_yaxes(title_text="Tiempo (min)", secondary_y=False, color=self.config.COLORS['primary'])
        fig.update_yaxes(title_text="Frecuencia (x/día)", secondary_y=True, color=self.config.COLORS['danger'])

        fig.update_layout(
            title="Curvas de Sensibilidad",
            template=self.config.LAYOUT_TEMPLATE,
            height=self.config.DEFAULT_HEIGHT,
            hovermode='x unified',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            font=dict(family=self.config.FONT_FAMILY)
        )

        st.plotly_chart(fig, use_container_width=True)

        # Métricas de sensibilidad
        self._show_sensitivity_metrics(values, tiempos, frecuencias, var_to_analyze)

        # Diagrama de tornado
        if st.checkbox("🌪️ Ver Diagrama de Tornado (todas las variables)", value=False):
            self._plot_tornado_diagram(base_scenario)

    def _show_sensitivity_metrics(self, values: np.ndarray, tiempos: List[float], frecuencias: List[float], var_name: str) -> None:
        """Muestra métricas de sensibilidad"""

        st.markdown("#### 📊 Métricas de Sensibilidad")

        # Calcular gradientes (derivadas numéricas)
        tiempo_gradient = np.gradient(tiempos, values)
        freq_gradient = np.gradient(frecuencias, values)

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            max_slope_t = np.max(np.abs(tiempo_gradient))
            st.metric(
                "Pendiente Máx (Tiempo)",
                f"{max_slope_t:.3f}",
                help="Máximo cambio en tiempo por unidad de variable"
            )

        with col2:
            max_slope_f = np.max(np.abs(freq_gradient))
            st.metric(
                "Pendiente Máx (Freq)",
                f"{max_slope_f:.3f}",
                help="Máximo cambio en frecuencia por unidad de variable"
            )

        with col3:
            variability_t = np.std(tiempos) / (np.mean(tiempos) + 0.001)
            st.metric(
                "Variabilidad (Tiempo)",
                f"{variability_t:.2f}",
                help="Coeficiente de variación"
            )

        with col4:
            variability_f = np.std(frecuencias) / (np.mean(frecuencias) + 0.001)
            st.metric(
                "Variabilidad (Freq)",
                f"{variability_f:.2f}",
                help="Coeficiente de variación"
            )

        # Gráfico de gradientes
        with st.expander("📉 Ver Gradientes (Derivadas)"):
            fig_grad = go.Figure()

            fig_grad.add_trace(go.Scatter(
                x=values[:-1],
                y=tiempo_gradient[:-1],
                name="∂Tiempo/∂" + var_name,
                line=dict(color=self.config.COLORS['primary'], width=2)
            ))

            fig_grad.add_trace(go.Scatter(
                x=values[:-1],
                y=freq_gradient[:-1],
                name="∂Frecuencia/∂" + var_name,
                line=dict(color=self.config.COLORS['danger'], width=2)
            ))

            fig_grad.update_layout(
                title="Sensibilidad Local (Gradientes)",
                xaxis_title=var_name,
                yaxis_title="Tasa de Cambio",
                template=self.config.LAYOUT_TEMPLATE,
                height=300,
                hovermode='x unified'
            )

            st.plotly_chart(fig_grad, use_container_width=True)

    def _plot_tornado_diagram(self, base_scenario: Dict[str, float]) -> None:
        """Diagrama de tornado comparando sensibilidad de todas las variables"""

        st.markdown("#### 🌪️ Diagrama de Tornado")
        st.markdown("Compara la sensibilidad de todas las variables simultáneamente")

        variables = {
            'temperature': ('🌡️ Temperatura', (0, 50)),
            'soil_humidity': ('🌱 Humedad Suelo', (0, 100)),
            'rain_probability': ('🌧️ Prob. Lluvia', (0, 100)),
            'air_humidity': ('💨 Humedad Aire', (0, 100)),
            'wind_speed': ('🍃 Viento', (0, 40))
        }

        results = []

        def safe_calculate_irrigation(scenario):
            """Calcula riego de forma segura con manejo de errores"""
            try:
                return self.system.calculate_irrigation(**scenario)
            except ValueError as e:
                if "Crisp output cannot be calculated" in str(e):
                    # Devolver valores por defecto cuando el sistema es too sparse
                    st.warning(f"⚠️ Valores límites detectados en el rango de {scenario['temperature']:.0f}°C, {scenario['soil_humidity']:.0f}% humedad. Usando valores aproximados.")
                    return (15.0, 2.0, {})  # Valores conservadores por defecto
                else:
                    raise e

        with st.spinner("Calculando impacto de todas las variables..."):
            for var_name, (display_name, (min_val, max_val)) in variables.items():
                # Valor base
                scenario_base = base_scenario.copy()
                t_base, f_base, _ = safe_calculate_irrigation(scenario_base)

                # Valor mínimo - usar valores más conservadores para evitar sparse
                min_val_safe = min(min_val, base_scenario.get(var_name, min_val) * 0.8)  # Mínimo al 80% del valor base
                scenario_min = base_scenario.copy()
                scenario_min[var_name] = max(min_val_safe, min_val * 0.1 if var_name in ['temperature'] else min_val)

                t_min, f_min, _ = safe_calculate_irrigation(scenario_min)

                # Valor máximo - usar valores más conservadores
                max_val_safe = max(max_val, base_scenario.get(var_name, max_val) * 1.3)  # Máximo al 130% del valor base
                scenario_max = base_scenario.copy()
                scenario_max[var_name] = min(max_val_safe, max_val)

                t_max, f_max, _ = safe_calculate_irrigation(scenario_max)

                # Calcular impacto
                impact_t = abs(t_max - t_min)
                impact_f = abs(f_max - f_min)

                results.append({
                    'variable': display_name,
                    'tiempo_min': t_min - t_base,
                    'tiempo_max': t_max - t_base,
                    'freq_min': f_min - f_base,
                    'freq_max': f_max - f_base,
                    'impact_t': impact_t,
                    'impact_f': impact_f
                })

        # Ordenar por impacto total
        results.sort(key=lambda x: x['impact_t'] + x['impact_f'], reverse=True)

        # Crear diagrama de tornado
        fig = go.Figure()

        var_names = [r['variable'] for r in results]

        # Barras negativas (min)
        fig.add_trace(go.Bar(
            y=var_names,
            x=[-r['tiempo_min'] for r in results],
            name='Tiempo (Mín)',
            orientation='h',
            marker=dict(color=self.config.COLORS['primary']),
            text=[f"{-r['tiempo_min']:.1f}" for r in results],
            textposition='inside'
        ))

        # Barras positivas (max)
        fig.add_trace(go.Bar(
            y=var_names,
            x=[r['tiempo_max'] for r in results],
            name='Tiempo (Máx)',
            orientation='h',
            marker=dict(color=self.config.COLORS['info']),
            text=[f"+{r['tiempo_max']:.1f}" for r in results],
            textposition='inside'
        ))

        fig.update_layout(
            title="Impacto en Tiempo de Riego",
            xaxis_title="Cambio en Tiempo (min)",
            barmode='overlay',
            template=self.config.LAYOUT_TEMPLATE,
            height=400,
            font=dict(family=self.config.FONT_FAMILY)
        )

        st.plotly_chart(fig, use_container_width=True)

        # Tabla de impactos
        with st.expander("📋 Ver tabla de impactos"):
            import pandas as pd
            df_impact = pd.DataFrame([
                {
                    'Variable': r['variable'],
                    'Impacto Tiempo': f"{r['impact_t']:.2f} min",
                    'Impacto Frecuencia': f"{r['impact_f']:.2f} x/día",
                    'Impacto Total': f"{r['impact_t'] + r['impact_f']:.2f}"
                }
                for r in results
            ])
            st.dataframe(df_impact, use_container_width=True)
