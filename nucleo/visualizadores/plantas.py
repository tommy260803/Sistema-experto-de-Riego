"""
Visualizaciones de Comparación de Plantas
Especializado en visualizaciones comparativas de especies vegetales
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
from ..base_conocimientos import PLANT_KB


class VisualizadorPlantas:
    """
    Visualizador especializado en comparación de plantas
    Maneja todas las visualizaciones relacionadas con especies vegetales
    """

    def __init__(self, config: VisualizationConfig):
        """
        Inicializa el visualizador de plantas

        Args:
            config: Configuración de visualización
        """
        self.config = config

    def plot_comparison(self) -> None:
        """Módulo completo de comparación de plantas"""

        st.markdown("### 🌱 Comparación de Requerimientos por Planta")
        st.markdown("Análisis comparativo de las necesidades hídricas de diferentes especies")

        plants = list(PLANT_KB.keys())

        # Selector múltiple
        col1, col2 = st.columns([3, 1])
        with col1:
            selected = st.multiselect(
                "Selecciona plantas a comparar",
                plants,
                default=plants[:min(4, len(plants))],
                label_visibility="collapsed"
            )

        with col2:
            view_type = st.radio(
                "Vista",
                ["Barras", "Radar", "Tabla"],
                label_visibility="collapsed"
            )

        if len(selected) < 1:
            st.info("ℹ️ Selecciona al menos 1 planta para ver su información")
            return

        if view_type == "Barras":
            self._plot_plant_bars(selected)
        elif view_type == "Radar":
            self._plot_plant_radar(selected)
        else:
            self._show_plant_table(selected)

    def _plot_plant_bars(self, selected: List[str]) -> None:
        """Gráfico de barras agrupadas"""

        # Crear subplots para diferentes métricas
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                "💧 Humedad Suelo Óptima (%)",
                "🌡️ Rango de Temperatura (°C)",
                "🏜️ Tolerancia a Sequía",
                "⏱️ Frecuencia de Riego"
            ),
            specs=[[{'type': 'bar'}, {'type': 'bar'}],
                   [{'type': 'bar'}, {'type': 'bar'}]]
        )

        colors = px.colors.qualitative.Set2

        for idx, plant in enumerate(selected):
            data = PLANT_KB[plant]
            color = colors[idx % len(colors)]

            # Humedad suelo (min, óptimo, max)
            hum_opt = data.get('humedad_suelo_opt', [40, 60])
            fig.add_trace(
                go.Bar(
                    name=plant,
                    x=['Mínimo', 'Óptimo', 'Máximo'],
                    y=[hum_opt[0], np.mean(hum_opt), hum_opt[1] if len(hum_opt) > 1 else np.mean(hum_opt)],
                    marker_color=color,
                    showlegend=(idx == 0),
                    text=[f"{hum_opt[0]}", f"{np.mean(hum_opt):.0f}", f"{hum_opt[1] if len(hum_opt) > 1 else np.mean(hum_opt):.0f}"],
                    textposition='outside'
                ),
                row=1, col=1
            )

            # Temperatura (min, max)
            temp_range = data.get('temp_range', [15, 30])
            fig.add_trace(
                go.Bar(
                    name=plant,
                    x=['Mínimo', 'Máximo'],
                    y=temp_range,
                    marker_color=color,
                    showlegend=False,
                    text=[f"{temp_range[0]}", f"{temp_range[1]}"],
                    textposition='outside'
                ),
                row=1, col=2
            )

            # Tolerancia (simulado - ajustar según tus datos)
            tolerancia = data.get('tolerancia_sequia', 5)
            fig.add_trace(
                go.Bar(
                    name=plant,
                    x=[plant],
                    y=[tolerancia],
                    marker_color=color,
                    showlegend=False,
                    text=[f"{tolerancia}/10"],
                    textposition='outside'
                ),
                row=2, col=1
            )

            # Frecuencia
            freq = data.get('frecuencia_riego', 2)
            fig.add_trace(
                go.Bar(
                    name=plant,
                    x=[plant],
                    y=[freq],
                    marker_color=color,
                    showlegend=False,
                    text=[f"{freq}x/día"],
                    textposition='outside'
                ),
                row=2, col=2
            )

        fig.update_layout(
            height=700,
            template=self.config.LAYOUT_TEMPLATE,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            font=dict(family=self.config.FONT_FAMILY)
        )

        fig.update_yaxes(range=[0, 110], row=1, col=1)
        fig.update_yaxes(range=[0, 50], row=1, col=2)

        st.plotly_chart(fig, use_container_width=True)

    def _plot_plant_radar(self, selected: List[str]) -> None:
        """Gráfico radar comparativo"""

        fig = go.Figure()

        categories = ['Hum. Suelo', 'Temperatura', 'Tolerancia', 'Frecuencia', 'Adaptabilidad']

        colors = px.colors.qualitative.Set2

        for idx, plant in enumerate(selected):
            data = PLANT_KB[plant]

            # Normalizar valores a escala 0-1
            values = [
                np.mean(data.get('humedad_suelo_opt', [50, 70])) / 100,
                np.mean(data.get('temp_range', [20, 30])) / 40,
                data.get('tolerancia_sequia', 5) / 10,
                data.get('frecuencia_riego', 2) / 5,
                data.get('adaptabilidad', 0.5)
            ]

            fig.add_trace(go.Scatterpolar(
                r=values + [values[0]],
                theta=categories + [categories[0]],
                fill='toself',
                name=plant,
                line=dict(color=colors[idx % len(colors)], width=2),
                marker=dict(size=8)
            ))

        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 1],
                    tickmode='linear',
                    tick0=0,
                    dtick=0.2
                )
            ),
            showlegend=True,
            template=self.config.LAYOUT_TEMPLATE,
            height=500,
            font=dict(family=self.config.FONT_FAMILY),
            title="Perfil de Requerimientos Normalizado"
        )

        st.plotly_chart(fig, use_container_width=True)

    def _show_plant_table(self, selected: List[str]) -> None:
        """Tabla comparativa detallada"""

        st.markdown("#### 📋 Tabla Comparativa Detallada")

        table_data = []
        for plant in selected:
            data = PLANT_KB[plant]
            hum_opt = data.get('humedad_suelo_opt', [0, 0])
            table_data.append({
                'Planta': plant,
                'Humedad Suelo (%)': f"{hum_opt[0]}-{hum_opt[1]}" if len(hum_opt) > 1 else f"{hum_opt[0]}",
                'Temperatura (°C)': f"{data.get('temp_range', [0, 0])[0]}-{data.get('temp_range', [0, 0])[1]}",
                'Tolerancia Sequía': f"{data.get('tolerancia_sequia', 0)}/10",
                'Frecuencia': f"{data.get('frecuencia_riego', 0)}x/día",
                'Consumo Agua': f"{data.get('consumo_agua', 0)} L/día"
            })

        import pandas as pd
        df = pd.DataFrame(table_data)

        # Estilizar tabla
        st.dataframe(
            df,
            use_container_width=True,
            height=(len(selected) + 1) * 35 + 38
        )

        # Botón de descarga
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Descargar CSV",
            data=csv,
            file_name="comparacion_plantas.csv",
            mime="text/csv"
        )
