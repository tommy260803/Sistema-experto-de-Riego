"""
Visualizaciones de Superficies 3D
Especializado en gráficos de superficies de control 3D
"""

from __future__ import annotations
from typing import Dict, List, Optional, Tuple
import numpy as np

try:
    import streamlit as st
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
except ImportError as e:
    raise ImportError(f"Missing required packages: {e}")

from .configuracion import VisualizationConfig
from ..motor_difuso import SistemaRiegoDifuso


class VisualizadorSuperficies:
    """
    Visualizador especializado en superficies de control 3D
    Maneja todas las visualizaciones relacionadas con análisis 3D
    """

    def __init__(self, system: SistemaRiegoDifuso, config: VisualizationConfig):
        """
        Inicializa el visualizador de superficies

        Args:
            system: Instancia del sistema de riego difuso
            config: Configuración de visualización
        """
        self.system = system
        self.config = config

    def plot_surfaces(self) -> None:
        """Módulo completo de superficies de control 3D"""

        st.markdown("### 🌐 Superficies de Control 3D")
        st.markdown("Visualización de la relación entre variables de entrada y salidas del sistema")

        # Configuración inline
        st.markdown("#### ⚙️ Configuración 3D")

        col1, col2, col3 = st.columns(3)

        with col1:
            # Variables a graficar
            var_options = {
                "Temperatura": "temperature",
                "Humedad Suelo": "soil_humidity",
                "Prob. Lluvia": "rain_probability",
                "Humedad Aire": "air_humidity",
                "Viento": "wind_speed"
            }

            var1_display = st.selectbox("Variable X", list(var_options.keys()), index=0)
            var2_display = st.selectbox("Variable Y", list(var_options.keys()), index=1)

        with col2:
            output = st.radio("Salida", ["Tiempo (min)", "Frecuencia (x/día)"])
            colorscale = st.selectbox(
                "Paleta de colores",
                ["Viridis", "Plasma", "Turbo", "RdYlGn_r", "Blues", "Reds"],
                index=0
            )

        with col3:
            resolution = st.slider("Resolución", 20, 60, 35, help="Mayor = más suave pero más lento")
            show_contour = st.checkbox("Proyección de contorno", True)

        var1 = var_options[var1_display]
        var2 = var_options[var2_display]
        output_type = "tiempo" if "Tiempo" in output else "frecuencia"

        st.markdown("### 🔒 Variables Fijas")

        # Variables fijas en grid
        fixed_vars = [key for key in var_options.keys() if var_options[key] not in [var1, var2]]
        if fixed_vars:
            cols = st.columns(len(fixed_vars))
            fixed_params = {}
            for i, display_name in enumerate(fixed_vars):
                param_name = var_options[display_name]
                default_val = self._get_default_value(param_name)
                max_val = self._get_max_value(param_name)
                with cols[i]:
                    fixed_params[param_name] = st.slider(
                        display_name,
                        0.0,
                        max_val,
                        default_val,
                        step=1.0
                    )
        else:
            fixed_params = {}

        # Generar superficie
        with st.spinner("🎨 Generando superficie 3D..."):
            try:
                X, Y, Z = self._generate_surface_data(
                    var1, var2, output_type, resolution, fixed_params
                )

                # Verificar que tenemos datos válidos
                if Z is None or Z.size == 0:
                    st.error("❌ Error: No se pudieron generar datos para la superficie")
                    return

            except Exception as e:
                st.error(f"❌ Error generando datos 3D: {e}")
                return

        # Limpiar datos problemáticos
        Z = np.nan_to_num(Z, nan=0.0, posinf=60.0, neginf=0.0)

        try:
            # Crear figura
            fig = go.Figure()

            # Superficie principal
            fig.add_trace(go.Surface(
                x=X, y=Y, z=Z,
                colorscale=colorscale,
                name='Control Surface',
                hovertemplate=(
                    f'<b>{var1_display}</b>: %{{x:.1f}}<br>'
                    f'<b>{var2_display}</b>: %{{y:.1f}}<br>'
                    f'<b>{output}</b>: %{{z:.2f}}<br>'
                    '<extra></extra>'
                ),
                colorbar=dict(
                    title=output
                )
            ))

        except Exception as e:
            st.error(f"❌ **Error al crear gráfico 3D**: {e}")
            st.info("Los datos generados contienen valores problemáticos (NaN, inf, etc.)")
            return

        # Proyección de contorno
        if show_contour:
            fig.add_trace(go.Contour(
                z=Z,
                x=X[0],
                y=Y[:, 0],
                colorscale=colorscale,
                showscale=False,
                opacity=0.4,
                contours=dict(
                    coloring='heatmap',
                    showlines=True,
                    showlabels=False
                ),
                hoverinfo='skip'
            ))

        # Layout
        fig.update_layout(
            scene=dict(
                xaxis=dict(
                    title=var1_display,
                    backgroundcolor="rgb(230, 230,230)",
                    gridcolor="white",
                    showbackground=True,
                    zerolinecolor="white"
                ),
                yaxis=dict(
                    title=var2_display,
                    backgroundcolor="rgb(230, 230,230)",
                    gridcolor="white",
                    showbackground=True,
                    zerolinecolor="white"
                ),
                zaxis=dict(
                    title=output,
                    backgroundcolor="rgb(230, 230,230)",
                    gridcolor="white",
                    showbackground=True,
                    zerolinecolor="white"
                ),
                camera=dict(
                    eye=dict(x=1.5, y=1.5, z=1.3),
                    center=dict(x=0, y=0, z=-0.1)
                )
            ),
            template=self.config.LAYOUT_TEMPLATE,
            height=self.config.SURFACE_HEIGHT,
            margin=dict(l=0, r=0, t=40, b=0),
            title=dict(
                text=f"Superficie de Control: {var1_display} × {var2_display} → {output}",
                font=dict(size=self.config.TITLE_FONT_SIZE, family=self.config.FONT_FAMILY),
                x=0.5,
                xanchor='center'
            )
        )

        st.plotly_chart(fig, use_container_width=True)

        # Análisis estadístico de la superficie
        self._show_surface_analysis(Z, output, var1_display, var2_display)

        # Comparación lado a lado
        if st.checkbox("🔀 Comparar Tiempo vs Frecuencia", value=False):
            self._plot_surface_comparison(var1, var2, resolution, fixed_params, colorscale)

    def _generate_surface_data(
        self,
        var1: str,
        var2: str,
        output: str,
        resolution: int,
        fixed_params: Dict[str, float]
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
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

    def _show_surface_analysis(self, Z: np.ndarray, output: str, var1: str, var2: str) -> None:
        """Muestra análisis estadístico de la superficie"""

        st.markdown("#### 📊 Análisis Estadístico de la Superficie")

        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            st.metric("Mínimo", f"{Z.min():.2f}", help="Valor mínimo en la superficie")
        with col2:
            st.metric("Máximo", f"{Z.max():.2f}", help="Valor máximo en la superficie")
        with col3:
            st.metric("Promedio", f"{Z.mean():.2f}", help="Valor promedio")
        with col4:
            st.metric("Desv. Std", f"{Z.std():.2f}", help="Desviación estándar")
        with col5:
            st.metric("Rango", f"{Z.max() - Z.min():.2f}", help="Diferencia máx-mín")

        # Histograma de distribución
        with st.expander("📈 Ver distribución de valores"):
            fig_hist = go.Figure()
            fig_hist.add_trace(go.Histogram(
                x=Z.flatten(),
                nbinsx=30,
                marker_color=self.config.COLORS['primary'],
                name='Distribución'
            ))
            fig_hist.update_layout(
                title="Distribución de Valores en la Superficie",
                xaxis_title=output.capitalize(),
                yaxis_title="Frecuencia",
                template=self.config.LAYOUT_TEMPLATE,
                height=300
            )
            st.plotly_chart(fig_hist, use_container_width=True)

    def _plot_surface_comparison(
        self,
        var1: str,
        var2: str,
        resolution: int,
        fixed_params: Dict,
        colorscale: str
    ) -> None:
        """Compara superficies de tiempo y frecuencia lado a lado"""

        st.markdown("#### ⚖️ Comparación: Tiempo vs Frecuencia")

        with st.spinner("Generando comparación..."):
            X, Y, Z_tiempo = self._generate_surface_data(var1, var2, 'tiempo', resolution, fixed_params)
            _, _, Z_freq = self._generate_surface_data(var1, var2, 'frecuencia', resolution, fixed_params)

        # Crear subplots
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=("⏱️ Tiempo de Riego (min)", "🔄 Frecuencia (riegos/día)"),
            specs=[[{'type': 'surface'}, {'type': 'surface'}]],
            horizontal_spacing=0.05
        )

        # Superficie de tiempo
        fig.add_trace(
            go.Surface(
                x=X, y=Y, z=Z_tiempo,
                colorscale='Blues',
                showscale=True,
                colorbar=dict(x=0.45, len=0.75)
            ),
            row=1, col=1
        )

        # Superficie de frecuencia
        fig.add_trace(
            go.Surface(
                x=X, y=Y, z=Z_freq,
                colorscale='Reds',
                showscale=True,
                colorbar=dict(x=1.02, len=0.75)
            ),
            row=1, col=2
        )

        # Layout
        fig.update_layout(
            height=500,
            template=self.config.LAYOUT_TEMPLATE,
            scene=dict(
                xaxis_title=var1,
                yaxis_title=var2,
                zaxis_title="Tiempo",
                camera=dict(eye=dict(x=1.3, y=1.3, z=1.2))
            ),
            scene2=dict(
                xaxis_title=var1,
                yaxis_title=var2,
                zaxis_title="Frecuencia",
                camera=dict(eye=dict(x=1.3, y=1.3, z=1.2))
            )
        )

        st.plotly_chart(fig, use_container_width=True)

    def _get_default_value(self, param_name: str) -> float:
        """Valor por defecto según parámetro, usando valores de calculadora si disponibles"""
        # Primero intentar obtener valores de la calculadora
        calc_current = st.session_state.get('calculadora_current', {})

        # Mapear nombres de parámetros
        param_mapping = {
            'temperature': 'temperature',
            'soil_humidity': 'soil_humidity',
            'rain_probability': 'rain_probability',
            'air_humidity': 'air_humidity',
            'wind_speed': 'wind_speed'
        }

        mapped_param = param_mapping.get(param_name, param_name)

        # Si hay valor de calculadora, usarlo
        if mapped_param in calc_current:
            return float(calc_current[mapped_param])

        # Valores por defecto estándar
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
