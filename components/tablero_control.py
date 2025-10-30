from __future__ import annotations
import streamlit as st
import plotly.graph_objects as go
from nucleo.motor_difuso import SistemaRiegoDifuso
from nucleo.base_conocimientos import PLANT_KB, PLANTS, get_recomendacion
from nucleo.utilidades import validate_inputs, save_history, timestamp, estimate_water_saving, logger

_engine = SistemaRiegoDifuso()


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


def _confidence_gauge(confianza: float):
    """Gauge de nivel de confianza con colores."""
    color = "red" if confianza < 0.4 else "yellow" if confianza < 0.7 else "green"
    return go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=confianza,
            title={"text": "Confianza"},
            domain={'x': [0, 1], 'y': [0, 1]},
            gauge={
                'axis': {'range': [0, 1]},
                'bar': {'color': color},
                'steps': [
                    {'range': [0, 0.4], 'color': "lightcoral"},
                    {'range': [0.4, 0.7], 'color': "lightyellow"},
                    {'range': [0.7, 1], 'color': "lightgreen"}
                ],
            },
            number={'valueformat': '.2f'}
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
            logger.info(f"Irrigation calculation initiated for plant {planta} with inputs: "
                        f"temp={temperatura}, soil_humidity={humedad_suelo}, rain_prob={prob_lluvia}, "
                        f"air_humidity={humedad_ambiental}, wind={viento}")

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
                logger.info(f"Irrigation decision for {planta}: time={t:.2f} min, frequency={f:.2f} x/day")
        except Exception as e:
            logger.error(f"Error during irrigation calculation: {e}")
            st.error(f"❌ Error: {e}")
            st.info("💡 Verifica que todos los valores estén en los rangos correctos.")
            return

        # Calcular confianza aproximada basada en la dispersión de activaciones
        confianza = min(1.0, sum(act.values()) / len(act)) if act else 0.8

        # Mostrar alerta de confianza baja
        if confianza < 0.5:
            st.warning(
                "⚠️ **Confianza Baja** - Las condiciones ambientales son ambiguas. "
                "Considera verificar manualmente o ajustar parámetros."
            )

        # Mostrar métricas principales con gauge de confianza
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.plotly_chart(_gauge("Tiempo de Riego", t, 0, 60, " min"), use_container_width=True)
        with c2:
            st.plotly_chart(_gauge("Frecuencia Diaria", f, 0, 4, " x"), use_container_width=True)
        with c3:
            st.plotly_chart(_confidence_gauge(confianza), use_container_width=True)
        with c4:
            # Estado y consejos
            status = "Óptimo"
            color = "green"
            if t > 30 or f >= 3:
                status = "Urgente"; color = "red"
            elif t > 15 or f >= 2:
                status = "Moderado"; color = "orange"

            st.markdown(f"### Estado: :{color}[{status}]")
            st.caption(f"**{planta}**")
            st.caption(kb.get('consejos', ''))

        # Ahorro de agua
        ahorro = estimate_water_saving(t, f)
        st.success(f"💧 **Ahorro estimado:** {ahorro} L/semana vs. riego tradicional")

        # Explicación detallada
        st.markdown("---")
        st.subheader("📋 Explicación de la Decisión")
        st.markdown(expl)

        # Guardar en histórico con confianza
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
            "confianza": round(confianza, 2),
        }
        save_history(record)

        # Ajuste por planta (educativo)
        st.markdown("---")
        st.subheader("🌱 Ajuste Personalizado por Planta")
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

        col_a, col_b = st.columns(2)
        with col_a:
            st.metric(
                label="Tiempo Ajustado",
                value=f"{reco['tiempo_ajustado']:.1f} min",
                delta=f"{reco['tiempo_ajustado'] - t:.1f} min"
            )
        with col_b:
            st.metric(
                label="Frecuencia Ajustada",
                value=f"{reco['frecuencia']:.2f} x/día",
                delta=f"{reco['frecuencia'] - f:.2f}"
            )

        # Alertas basadas en condiciones
        if temperatura > 35:
            st.error("⚠️ Alta temperatura detectada. Riesgo de estrés hídrico en plantas.")
        if humedad_suelo < 20:
            st.warning("⚠️ Humedad del suelo muy baja. Se recomienda riego urgente.")
        if t > 30:
            st.warning("⚠️ Tiempo de riego excesivo recomendado. Verifica condiciones ambientales.")

        st.info(
            f"Tiempo ajustado para {planta}: {reco['tiempo_ajustado']:.1f} min | Frecuencia: {reco['frecuencia']:.2f} x/día"
        )

        # Reglas más activas con visualización mejorada
        with st.expander("🔍 Ver Reglas Fuzzy Activadas (Top 10)"):
            sorted_rules = sorted(act.items(), key=lambda kv: kv[1], reverse=True)[:10]

            # Crear visualización de barras horizontal
            fig = go.Figure(go.Bar(
                x=[v for _, v in sorted_rules],
                y=[k for k, _ in sorted_rules],
                orientation='h',
                marker=dict(
                    color=[v for _, v in sorted_rules],
                    colorscale='Viridis',
                    showscale=True,
                    colorbar=dict(title="Activación")
                ),
                text=[f"{v:.3f}" for _, v in sorted_rules],
                textposition='auto',
            ))
            fig.update_layout(
                title="Nivel de Activación por Regla Fuzzy",
                xaxis_title="Activación (0-1)",
                yaxis_title="Regla",
                height=400,
                showlegend=False,
                yaxis={'categoryorder': 'total ascending'}
            )
            st.plotly_chart(fig, use_container_width=True)

            # Tabla adicional con detalle
            st.table({
                "Regla": [k for k, _ in sorted_rules],
                "Activación": [round(v, 3) for _, v in sorted_rules],
                "Impacto": ["Bajo" if v < 0.3 else "Medio" if v < 0.7 else "Alto" for _, v in sorted_rules]
            })

        # Botón para limpiar cache (útil para debugging)
        if st.button("🔄 Limpiar Cache del Motor", help="Útil si cambias el código del motor fuzzy"):
            if hasattr(_engine, '_cache'):
                _engine._cache.clear()
                st.success("💾 Cache limpiado exitosamente")
            else:
                st.info("No hay cache para limpiar")
