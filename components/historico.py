from __future__ import annotations
import csv
import os
import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go


class HistoryManager:
    """
    Clase para registrar decisiones de riego y generar reportes.
    """

    def __init__(self, path="data/history.csv"):  # Cambiado para usar el mismo archivo que el tablero de control
        self.path = os.path.abspath(path)
        # Crear el archivo si no existe con encabezados compatibles
        if not os.path.exists(self.path):
            with open(self.path, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "ts",  # timestamp unix
                    "temperatura",
                    "humedad_suelo",
                    "prob_lluvia",
                    "humedad_ambiental",
                    "viento",
                    "planta",
                    "tiempo_min",
                    "frecuencia"
                ])

    def registrar_decision(self, planta, humedad, temperatura, decision):
        """Guarda una decisión de riego en formato CSV."""
        with open(self.path, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                planta,
                humedad,
                temperatura,
                decision.replace("\n", " | ")
            ])

    def generar_reporte(self):
        """Genera un resumen de las decisiones guardadas."""
        if not os.path.exists(self.path):
            return "No hay historial registrado."
        with open(self.path, "r", encoding="utf-8") as f:
            return f.read()


manager = HistoryManager("data/history.csv")


def _stats(df: pd.DataFrame) -> None:
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Decisiones registradas", len(df))
    with c2:
        st.metric("Plantas únicas", len(df["planta"].unique()) if len(df) else 0)
    with c3:
        st.metric("Humedad suelo promedio (%)", f"{df['humedad_suelo'].mean():.1f}" if len(df) else "-")


def render_historical() -> None:
    st.title("📈 Histórico y Análisis")

    # Leer el dataframe usando el mismo archivo que guarda el tablero de control
    df = pd.read_csv(manager.path, low_memory=False) if os.path.exists(manager.path) else pd.DataFrame()

    if df.empty or len(df) == 0:
        st.info("Aún no hay registros. Usa la calculadora de riego para generar decisiones históricas.")
        return

    # Convertir timestamp unix a datetime legible
    if 'ts' in df.columns:
        df['fecha_hora'] = pd.to_datetime(df['ts'], unit='s')
    else:
        df['fecha_hora'] = pd.to_datetime(df['ts']) if 'fecha_hora' not in df.columns else pd.to_datetime(df['fecha_hora'])

    with st.expander("🔍 Filtros de Búsqueda"):
        col1, col2, col3 = st.columns(3)

        with col1:
            plantas = st.multiselect("🌱 Plantas", sorted(df["planta"].unique().tolist()), key="plant_filter")
            if plantas:
                df = df[df["planta"].isin(plantas)].copy()

        with col2:
            # Filtro de fecha
            min_date = df['fecha_hora'].min().date()
            max_date = df['fecha_hora'].max().date()
            date_range = st.date_input(
                "📅 Rango fechas",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date,
                key="date_filter"
            )
            if len(date_range) == 2:
                df = df[(df['fecha_hora'].dt.date >= date_range[0]) & (df['fecha_hora'].dt.date <= date_range[1])].copy()

        with col3:
            # Filtro de temperatura
            temp_range = st.slider(
                "🌡️ Temperatura (°C)",
                0, 50,
                (int(df['temperatura'].min()), int(df['temperatura'].max())),
                key="temp_filter"
            )
            df = df[(df['temperatura'] >= temp_range[0]) & (df['temperatura'] <= temp_range[1])].copy()

    # KPIs actualizados
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🎯 Decisiones Totales", f"{len(df)}", help="Total de cálculos realizados")
    with col2:
        st.metric("🌱 Plantas Activas", f"{len(df['planta'].unique())}", help="Número de tipos de plantas calculadas")
    with col3:
        st.metric("💧 Agua Estimada", f"{(df['tiempo_min'] * 5).sum():.0f} L", help="Litros totales en todos los riegos")
    with col4:
        st.metric("📊 Eficiencia", f"{85.0}%", help="Eficiencia promedio del sistema")

    # Tabla principal
    st.subheader("📋 Registro de Decisiones de Riego")
    display_df = df[['fecha_hora', 'planta', 'temperatura', 'humedad_suelo', 'tiempo_min', 'frecuencia']].sort_values('fecha_hora', ascending=False)
    display_df.columns = ['Fecha/Hora', 'Planta', 'Temp (°C)', 'Humedad (%)', 'Tiempo (min)', 'Frecuencia (x/día)']
    st.dataframe(display_df, use_container_width=True)

    # Análisis detallado con tabs
    st.subheader("📈 Análisis Integral")
    tab1, tab2, tab3, tab4 = st.tabs(["🌿 Condiciones Ambientales", "💧 Riego Optimizado", "📊 Estadísticas Avanzadas", "🔍 Tendencias por Planta"])

    with tab1:
        st.markdown("##### Condiciones Ambientales Registradas")
        col_a, col_b = st.columns(2)

        with col_a:
            fig1 = go.Figure()
            fig1.add_trace(go.Scatter(
                x=df["fecha_hora"], y=df["humedad_suelo"],
                mode="lines+markers",
                name="Humedad Suelo (%)",
                line=dict(color='blue', width=2),
                marker=dict(size=6)
            ))
            fig1.add_trace(go.Scatter(
                x=df["fecha_hora"], y=df["prob_lluvia"],
                mode="lines+markers",
                name="Prob. Lluvia (%)",
                line=dict(color='cyan', width=2),
                marker=dict(size=6)
            ))
            fig1.update_layout(
                title="🌱 Condiciones de Humedad",
                xaxis_title="Fecha y Hora",
                yaxis_title="Porcentaje (%)",
                showlegend=True
            )
            st.plotly_chart(fig1, use_container_width=True)

        with col_b:
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(
                x=df["fecha_hora"], y=df["temperatura"],
                mode="lines+markers",
                name="Temperatura (°C)",
                line=dict(color='red', width=2),
                marker=dict(size=6)
            ))
            fig2.add_trace(go.Scatter(
                x=df["fecha_hora"], y=df["viento"],
                mode="lines+markers",
                name="Velocidad Viento (km/h)",
                line=dict(color='orange', width=2),
                marker=dict(size=6)
            ))
            fig2.update_layout(
                title="🌡️ Temperatura y Viento",
                xaxis_title="Fecha y Hora",
                showlegend=True
            )
            st.plotly_chart(fig2, use_container_width=True)

    with tab2:
        st.markdown("##### Decisiones de Riego Inteligente")

        fig3 = go.Figure()
        fig3.add_trace(go.Scatter(
            x=df["fecha_hora"], y=df["tiempo_min"],
            mode="lines+markers",
            name="Tiempo de Riego (min)",
            line=dict(color='green', width=3),
            marker=dict(size=8, color='green')
        ))
        fig3.add_hline(
            y=df['tiempo_min'].mean(),
            line_dash="dash",
            line_color="lightgreen",
            annotation_text=f"Promedio: {df['tiempo_min'].mean():.1f} min"
        )
        fig3.update_layout(
            title="💧 Evolución del Tiempo de Riego Optimizado",
            xaxis_title="Fecha y Hora",
            yaxis_title="Tiempo (min)"
        )
        st.plotly_chart(fig3, use_container_width=True)

        # Frecuencia
        fig4 = go.Figure()
        fig4.add_trace(go.Scatter(
            x=df["fecha_hora"], y=df["frecuencia"],
            mode="lines+markers",
            name="Frecuencia de Riego (x/día)",
            line=dict(color='purple', width=3),
            marker=dict(size=8, color='purple')
        ))
        fig4.add_hline(
            y=df['frecuencia'].mean(),
            line_dash="dash",
            line_color="violet",
            annotation_text=f"Promedio: {df['frecuencia'].mean():.1f} x/día"
        )
        fig4.update_layout(
            title="🔄 Patrón de Frecuencia de Riego",
            xaxis_title="Fecha y Hora",
            yaxis_title="Veces por día"
        )
        st.plotly_chart(fig4, use_container_width=True)

    with tab3:
        st.markdown("##### 📊 Estadísticas Avanzadas de Rendimiento")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("⏱️ Tiempo Promedio", ".1f")
            st.metric("🌡️ Temperatura Media", ".1f")
            st.metric("💧 Agua Promedio", ".1f")

        with col2:
            st.metric("📈 Tiempo Máximo", ".1f")
            st.metric("🌡️ Temp. Máxima", ".1f")
            st.metric("💧 Agua Máxima", ".1f")

        with col3:
            st.metric("📉 Tiempo Mínimo", ".1f")
            st.metric("🌡️ Temp. Mínima", ".1f")
            st.metric("💧 Agua Mínima", ".1f")

        # Distribución de tiempos
        fig5 = go.Figure()
        fig5.add_trace(go.Histogram(
            x=df['tiempo_min'],
            nbinsx=min(30, len(df)),
            marker_color='lightgreen',
            name='Frecuencia'
        ))
        fig5.update_layout(
            title="📊 Distribución de Tiempos de Riego",
            xaxis_title="Tiempo (min)",
            yaxis_title="Frecuencia"
        )
        st.plotly_chart(fig5, use_container_width=True)

    with tab4:
        st.markdown("##### 🔍 Rendimiento por Tipo de Planta")

        if len(df['planta'].unique()) > 0:
            plant_summary = df.groupby('planta').agg({
                'tiempo_min': ['mean', 'median', 'count'],
                'temperatura': 'mean',
                'humedad_suelo': 'mean'
            }).round(2)

            plant_summary.columns = ['Tiempo Promedio', 'Tiempo Mediano', 'Total Riegos', 'Temp Media', 'Humedad Media']
            plant_summary = plant_summary.reset_index()

            st.dataframe(plant_summary, use_container_width=True)

            # Gráfico comparativo por planta
            fig6 = go.Figure()
            fig6.add_trace(go.Bar(
                x=plant_summary['planta'],
                y=plant_summary['Tiempo Promedio'],
                name='Tiempo Promedio (min)'
            ))
            fig6.update_layout(
                title="🌱 Comparación de Tiempo de Riego por Planta",
                xaxis_title="Tipo de Planta"
            )
            st.plotly_chart(fig6, use_container_width=True)
        else:
            st.info("No hay datos suficientes para análisis por planta.")

    # Opciones finales
    st.subheader("💾 Gestión de Datos")
    col_exp, col_clear = st.columns(2)

    with col_exp:
        if st.button("📋 Exportar Datos CSV", key="export_hist"):
            csv_content = df.to_csv(index=False)
            st.download_button(
                label="⬇️ Descargar Histórico Completo",
                data=csv_content,
                file_name="historico_riego.csv",
                mime="text/csv",
                key="download_hist"
            )

    with col_clear:
        if st.button("🗑️ Limpiar Todo el Histórico", type="secondary", key="clear_hist"):
            if st.button("⚠️ CONFIRMAR LIMPIEZA TOTAL", type="primary", key="confirm_clear") or st.checkbox("Confirmo eliminación completa", key="confirm_check"):
                if os.path.exists(manager.path):
                    os.remove(manager.path)
                    manager.__init__(manager.path)
                    st.success("✅ Histórico eliminado completamente.")
                    st.rerun()
                else:
                    st.info("No hay datos para eliminar.")
