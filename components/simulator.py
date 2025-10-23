from __future__ import annotations
import json
import random
from typing import Dict, List
import streamlit as st
import pandas as pd
from src.fuzzy_engine import FuzzyIrrigationSystem
from src.knowledge_base import PLANT_KB, PLANTS

SCENARIOS_PATH = "data/escenarios_prueba.json"
_engine = FuzzyIrrigationSystem()

# Escenarios requeridos por la especificación
ESCENARIOS = {
    "☀️ Día Caluroso": {"temperatura": 38, "humedad_suelo": 25, "prob_lluvia": 5, "humedad_ambiental": 30, "viento": 10, "planta": "Tomate"},
    "🌧️ Día Lluvioso": {"temperatura": 18, "humedad_suelo": 80, "prob_lluvia": 90, "humedad_ambiental": 85, "viento": 12, "planta": "Lechuga"},
    "🌵 Clima Seco": {"temperatura": 32, "humedad_suelo": 20, "prob_lluvia": 10, "humedad_ambiental": 25, "viento": 15, "planta": "Cactus"},
    "❄️ Día Frío": {"temperatura": 10, "humedad_suelo": 60, "prob_lluvia": 30, "humedad_ambiental": 70, "viento": 8, "planta": "Rosa"},
    "🌪️ Día Ventoso": {"temperatura": 25, "humedad_suelo": 40, "prob_lluvia": 20, "humedad_ambiental": 45, "viento": 50, "planta": "Césped"},
    "🌤️ Condiciones Ideales": {"temperatura": 22, "humedad_suelo": 55, "prob_lluvia": 20, "humedad_ambiental": 50, "viento": 10, "planta": "Fresa"},
}


def run_simulation(nombre: str) -> Dict[str, float]:
    s = ESCENARIOS.get(nombre)
    if not s:
        return {}
    t, f, _ = _engine.calculate_irrigation(
        temperature=s["temperatura"],
        soil_humidity=s["humedad_suelo"],
        rain_probability=s["prob_lluvia"],
        air_humidity=s["humedad_ambiental"],
        wind_speed=s["viento"],
        ajuste_planta=PLANT_KB.get(s.get("planta", "Tomate"), {}).get("factor_ajuste", 1.0),
    )
    return {"tiempo_min": round(t, 2), "frecuencia": round(f, 2)}


def _load_scenarios() -> List[Dict]:
    try:
        with open(SCENARIOS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def render_simulator() -> None:
    st.title("🎮 Simulador de Escenarios")
    scenarios = _load_scenarios()

    st.subheader("Escenarios predefinidos")
    esc_names = list(ESCENARIOS.keys())
    nombre = st.selectbox("Seleccionar escenario", esc_names)

    st.json({"nombre": nombre, **ESCENARIOS[nombre]})

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Ejecutar todos**")
        if st.button("Calcular todos los escenarios"):
            rows = []
            for nom, s in ESCENARIOS.items():
                res = run_simulation(nom)
                rows.append({"Escenario": nom, "Planta": s.get("planta","Tomate"), "Tiempo(min)": res.get("tiempo_min",0), "Frecuencia": res.get("frecuencia",0)})
            st.dataframe(pd.DataFrame(rows))

    with col2:
        st.markdown("**Modo Desafío**")
        if "challenge" not in st.session_state:
            st.session_state["challenge"] = random.choice(list(ESCENARIOS.items())) if ESCENARIOS else None
        if st.button("Nuevo desafío"):
            st.session_state["challenge"] = random.choice(list(ESCENARIOS.items())) if ESCENARIOS else None
        ch = st.session_state.get("challenge")
        if ch:
            nom, data = ch
            st.write("Adivina el tiempo de riego para:")
            st.json({"nombre": nom, **data})
            guess = st.slider("Tu estimación (min)", 0.0, 60.0, 20.0)
            if st.button("Revelar"):
                res = run_simulation(nom)
                st.success(f"Tiempo real: {res['tiempo_min']:.1f} min; Diferencia: {abs(res['tiempo_min']-guess):.1f} min")
