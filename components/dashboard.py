from __future__ import annotations
import streamlit as st
import plotly.graph_objects as go
from src.fuzzy_engine import FuzzyIrrigationSystem
from src.knowledge_base import PLANT_KB, PLANTS, get_recomendacion
from src.utils import validate_inputs, save_history, timestamp, estimate_water_saving

_engine = FuzzyIrrigationSystem()


def _gauge(title: str, value: float, minv: float, maxv: float, suffix: str = ""):
    return go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=value,
            title={"text": title},
            gauge={"axis": {"range": [minv, maxv]}},
            number={"suffix": suffix},
        )
    )


def render_dashboard() -> None:
    st.title("🌊 Calculadora de Riego Inteligente")

    with st.expander("¿Qué es Lógica Difusa?", expanded=False):
        st.write(
            "La lógica difusa permite razonar con valores imprecisos como 'alto' o 'bajo'. "
            "Este sistema usa inferencia de Mamdani y centroide para decidir tiempo y frecuencia de riego."
        )

    cols = st.columns(3)
    with cols[0]:
        temperatura = st.slider("Temperatura (°C)", 0.0, 45.0, 25.0, help="0-45°C")
        humedad_suelo = st.slider("Humedad del Suelo (%)", 0.0, 100.0, 30.0)
    with cols[1]:
        prob_lluvia = st.slider("Probabilidad de Lluvia (%)", 0.0, 100.0, 10.0)
        humedad_ambiental = st.slider("Humedad Ambiental (%)", 0.0, 100.0, 40.0)
    with cols[2]:
        viento = st.slider("Velocidad del Viento (km/h)", 0.0, 50.0, 8.0)
        planta = st.selectbox("Tipo de planta", PLANTS, index=0)
        auto = st.toggle("Simulación Automática", value=False)

    kb = PLANT_KB.get(planta, {})
    ajuste = float(kb.get("factor_ajuste", 1.0))

    do_calc = st.button("Calcular Riego", type="primary") or auto

    if do_calc:
        try:
            validate_inputs(temperatura, humedad_suelo, prob_lluvia, humedad_ambiental, viento)
            with st.spinner("Calculando decisión de riego..."):
                t, f, act = _engine.calculate_irrigation(
                    temperature=temperatura,
                    soil_humidity=humedad_suelo,
                    rain_probability=prob_lluvia,
                    air_humidity=humedad_ambiental,
                    wind_speed=viento,
                    ajuste_planta=ajuste,
                )
                expl = _engine.explain_decision(t, f, act)
        except Exception as e:
            st.error(f"Error: {e}")
            return

        c1, c2, c3 = st.columns([1, 1, 1])
        with c1:
            st.plotly_chart(_gauge("Tiempo de Riego", t, 0, 60, " min"), use_container_width=True)
        with c2:
            st.plotly_chart(_gauge("Frecuencia Diaria", f, 0, 4, " x"), use_container_width=True)
        with c3:
            status = "Óptimo"
            color = "metric-green"
            if t > 30 or f >= 3:
                status = "Urgente"; color = "metric-red"
            elif t > 15 or f >= 2:
                status = "Moderado"; color = "metric-yellow"
            st.metric(label="Estado", value=status)
            st.markdown(f"<div class='{color}'>Recomendaciones para {planta}: {kb.get('consejos','')}</div>", unsafe_allow_html=True)

        ahorro = estimate_water_saving(t, f)
        st.metric(label="Ahorro de Agua estimado", value=f"{ahorro} L/semana")

        st.write(expl)

        record = {
            "ts": timestamp(),
            "temperatura": temperatura,
            "humedad_suelo": humedad_suelo,
            "prob_lluvia": prob_lluvia,
            "humedad_ambiental": humedad_ambiental,
            "viento": viento,
            "planta": planta,
            "tiempo_min": round(t, 2),
            "frecuencia": round(f, 2),
        }
        save_history(record)

        # Ajuste por planta (educativo) y despliegue
        reco = get_recomendacion(
            planta,
            {
                "temperatura": temperatura,
                "humedad_suelo": humedad_suelo,
                "prob_lluvia": prob_lluvia,
                "humedad_ambiente": humedad_ambiental,
                "velocidad_viento": viento,
            },
            {"tiempo_min": t, "frecuencia": f},
        )
        st.info(
            f"Tiempo ajustado para {planta}: {reco['tiempo_ajustado']:.1f} min | Frecuencia: {reco['frecuencia']:.2f} x/día"
        )

        with st.expander("Ver reglas más activas"):
            sorted_rules = sorted(act.items(), key=lambda kv: kv[1], reverse=True)[:10]
            st.table({"Regla": [k for k, _ in sorted_rules], "Activación": [round(v, 3) for _, v in sorted_rules]})
