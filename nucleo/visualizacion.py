from __future__ import annotations
from typing import Dict, List, Tuple
import numpy as np
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from .motor_difuso import (
    TEMP_UNIVERSE,
    SOIL_UNIVERSE,
    RAIN_UNIVERSE,
    AIRH_UNIVERSE,
    WIND_UNIVERSE,
    TIME_UNIVERSE,
    FREQ_UNIVERSE,
    SistemaRiegoDifuso,
)
from .base_conocimientos import PLANT_KB


def plot_membership_functions(system: SistemaRiegoDifuso) -> None:
    """Graficar todas las funciones de membresía (5 entradas + 2 salidas)."""
    st.subheader("Funciones de Membresía")
    grids = [
        ("Temperatura (°C)", TEMP_UNIVERSE, system.temperatura, ["baja", "media", "alta"]),
        ("Humedad Suelo (%)", SOIL_UNIVERSE, system.h_suelo, ["seca", "moderada", "humeda"]),
        ("Prob. Lluvia (%)", RAIN_UNIVERSE, system.lluvia, ["baja", "media", "alta"]),
        ("Humedad Ambiente (%)", AIRH_UNIVERSE, system.h_aire, ["baja", "media", "alta"]),
        ("Viento (km/h)", WIND_UNIVERSE, system.viento, ["bajo", "medio", "alto"]),
        ("Tiempo (min)", TIME_UNIVERSE, system.tiempo, ["nulo", "corto", "medio", "largo"]),
        ("Frecuencia (x/día)", FREQ_UNIVERSE, system.frecuencia, ["baja", "media", "alta"]),
    ]
    for i in range(0, len(grids), 2):
        cols = st.columns(2)
        for j in range(2):
            if i + j >= len(grids):
                break
            title, X, var, labels = grids[i + j]
            with cols[j]:
                fig = go.Figure()
                for label in labels:
                    fig.add_trace(go.Scatter(x=X, y=var[label].mf, name=label))
                fig.update_layout(title=title)
                st.plotly_chart(fig, use_container_width=True)


def plot_reglas_activadas(activaciones: Dict[str, float]) -> None:
    keys = list(activaciones.keys())
    vals = [activaciones[k] for k in keys]
    fig = go.Figure(go.Bar(x=keys, y=vals))
    fig.update_layout(title="Activación por regla")
    st.plotly_chart(fig, use_container_width=True)


def plot_gauge(valor: float, max_val: float, title: str = "") -> None:
    fig = go.Figure(
        go.Indicator(mode="gauge+number", value=valor, gauge={"axis": {"range": [0, max_val]}})
    )
    fig.update_layout(title=title)
    st.plotly_chart(fig, use_container_width=True)


def radar_inputs(vals: Dict[str, float]) -> None:
    labels = list(vals.keys())
    data = list(vals.values())
    fig = go.Figure(
        data=go.Scatterpolar(r=data + [data[0]], theta=labels + [labels[0]], fill="toself")
    )
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 1])), showlegend=False)
    st.plotly_chart(fig, use_container_width=True)


def render_visualizations_page() -> None:
    st.title("📊 Visualizaciones")
    try:
        sys = SistemaRiegoDifuso()
    except Exception as e:
        st.error(f"Error inicializando sistema de riego: {e}")
        return

    option = st.selectbox(
        "Selecciona visualización",
        [
            "Funciones de Membresía",
            "Superficie 3D",
            "Comparación de Plantas",
            "Histórico",
        ],
    )

    if option == "Funciones de Membresía":
        try:
            plot_membership_functions(sys)
            st.subheader("Activación de reglas (ejemplo)")
            act = sys.get_rule_activations(30, 25, 10, 30, 10)
            plot_reglas_activadas(act)
        except Exception as e:
            st.error(f"Error generando funciones de membresía: {e}")
    elif option == "Superficie 3D":
        try:
            # Test calculation
            test_t, test_f, _ = sys.calculate_irrigation(temperature=25.0, soil_humidity=40.0, rain_probability=20.0, air_humidity=50.0, wind_speed=10.0)
            st.write(f"Prueba de cálculo: tiempo={test_t:.2f}, frecuencia={test_f:.2f}")
            if test_t == 0.0 and test_f == 0.0:
                st.warning("El cálculo devuelve 0. Posibles issues en el motor fuzzy.")
            st.write("Superficie 3D: temperatura vs humedad_suelo -> tiempo")
            plot_surface_3d("temperatura", "humedad_suelo", "tiempo")
        except Exception as e:
            st.error(f"Error generando superficie 3D: {e}")
    elif option == "Comparación de Plantas":
        try:
            plot_comparacion_plantas()
        except Exception as e:
            st.error(f"Error generando comparación de plantas: {e}")
    elif option == "Histórico":
        try:
            import pandas as pd
            from .utilidades import load_history
            df = load_history()
            plot_historico(df)
        except Exception as e:
            st.error(f"Error cargando histórico: {e}")


def plot_surface_3d(var1: str, var2: str, output: str) -> None:
    """Superficie 3D aproximada evaluando el sistema en una grilla."""
    sys = SistemaRiegoDifuso()
    grid_x = np.linspace(0, 50, 30) if var1 == "temperatura" else np.linspace(0, 100, 30)
    grid_y = np.linspace(0, 100, 30)
    Z = np.zeros((len(grid_x), len(grid_y)))
    for i, x in enumerate(grid_x):
        for j, y in enumerate(grid_y):
            t, f, _ = sys.calculate_irrigation(
                temperature=float(x if var1 == "temperatura" else 25),
                soil_humidity=float(y if var2 == "humedad_suelo" else 40),
                rain_probability=20,
                air_humidity=40,
                wind_speed=10,
            )
            Z[i, j] = t if output == "tiempo" else f
    fig = go.Figure(data=[go.Surface(z=Z, x=grid_x, y=grid_y)])
    fig.update_layout(scene=dict(xaxis_title=var1, yaxis_title=var2, zaxis_title=output))
    st.plotly_chart(fig, use_container_width=True)


def plot_comparacion_plantas() -> None:
    labels = list(PLANT_KB.keys())
    humedad_min = [PLANT_KB[p]["humedad_suelo_opt"][0] for p in labels]
    humedad_max = [PLANT_KB[p]["humedad_suelo_opt"][1] for p in labels]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=labels, y=humedad_min, name="Hum. min"))
    fig.add_trace(go.Bar(x=labels, y=humedad_max, name="Hum. max"))
    fig.update_layout(barmode="group", title="Requerimientos de humedad por planta")
    st.plotly_chart(fig, use_container_width=True)


def plot_historico(df) -> None:
    if df is None or df.empty:
        st.info("No hay histórico disponible.")
        return
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["ts"], y=df["tiempo_min"], mode="lines+markers", name="Tiempo (min)"))
    fig.update_layout(title="Histórico de Tiempo de Riego")
    st.plotly_chart(fig, use_container_width=True)
