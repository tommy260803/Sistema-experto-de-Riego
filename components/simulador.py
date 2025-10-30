from __future__ import annotations
import json
import random
from typing import Dict, List, Optional
import streamlit as st
import pandas as pd
from nucleo.base_conocimientos import PLANT_KB, PLANTS

SCENARIOS_PATH = "data/escenarios_prueba.json"
_engine: Optional['SistemaRiegoDifuso'] = None

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
    """Función legacy para escenarios predefinidos"""
    s = ESCENARIOS.get(nombre)
    if not s:
        return {}
    try:
        from nucleo.motor_difuso import SistemaRiegoDifuso
        engine = SistemaRiegoDifuso()
        t, f, _ = engine.calculate_irrigation(
            temperature=s["temperatura"],
            soil_humidity=s["humedad_suelo"],
            rain_probability=s["prob_lluvia"],
            air_humidity=s["humedad_ambiental"],
            wind_speed=s["viento"],
            ajuste_planta=PLANT_KB.get(s.get("planta", "Tomate"), {}).get("factor_ajuste", 1.0),
        )
        return {"tiempo_min": round(t, 2), "frecuencia": round(f, 2)}
    except Exception as e:
        st.error(f"Error en simulación {nombre}: {e}")
        return {"tiempo_min": 15.0, "frecuencia": 2.0}


def run_simulation_custom(escenario: Dict) -> Dict[str, float]:
    """Nueva función para escenarios personalizados"""
    try:
        from nucleo.motor_difuso import SistemaRiegoDifuso
        engine = SistemaRiegoDifuso()
        t, f, _ = engine.calculate_irrigation(
            temperature=escenario["temperatura"],
            soil_humidity=escenario["humedad_suelo"],
            rain_probability=escenario["prob_lluvia"],
            air_humidity=escenario["humedad_ambiental"],
            wind_speed=escenario["viento"],
            ajuste_planta=PLANT_KB.get(escenario.get("planta", "Tomate"), {}).get("factor_ajuste", 1.0),
        )
        return {"tiempo_min": round(t, 2), "frecuencia": round(f, 2)}
    except Exception as e:
        st.error(f"Error en cálculo personalizado: {e}")
        return {"tiempo_min": 15.0, "frecuencia": 2.0}


def _load_scenarios() -> List[Dict]:
    try:
        with open(SCENARIOS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def render_simulator() -> None:
    st.title("🎮 Simulador de Escenarios")

    try:
        st.markdown("### 🎯 Simulador Interactivo de Condiciones de Riego")
        st.markdown("Prueba diferentes escenarios ambientales y observa cómo responde el sistema de riego inteligente.")

        # Escenario individual
        st.subheader("🌡️ Simulación Individual")
        col1, col2 = st.columns([1, 2])

        with col1:
            st.markdown("**Configurar Escenario**")
            esc_names = list(ESCENARIOS.keys())
            nombre = st.selectbox("Seleccionar escenario predefinido", esc_names, key="scenario_select")

            st.markdown("**O configurar manualmente**")
            use_custom = st.checkbox("Usar configuración personalizada", value=False, key="custom_scenario")

            if use_custom:
                temp_custom = st.slider("Temperatura (°C)", 0, 45, 25, key="temp_custom")
                hum_suelo_custom = st.slider("Humedad Suelo (%)", 0, 100, 50, key="hum_suelo_custom")
                prob_lluvia_custom = st.slider("Prob. Lluvia (%)", 0, 100, 20, key="lluvia_custom")
                hum_aire_custom = st.slider("Humedad Aire (%)", 0, 100, 60, key="hum_aire_custom")
                viento_custom = st.slider("Velocidad Viento (km/h)", 0, 50, 15, key="viento_custom")
                planta_custom = st.selectbox("Planta", PLANTS, index=0, key="planta_custom")

                escenario_actual = {
                    "temperatura": temp_custom,
                    "humedad_suelo": hum_suelo_custom,
                    "prob_lluvia": prob_lluvia_custom,
                    "humedad_ambiental": hum_aire_custom,
                    "viento": viento_custom,
                    "planta": planta_custom
                }
            else:
                escenario_actual = ESCENARIOS[nombre]

        with col2:
            st.markdown("**Condiciones del Escenario**")
            st.json(escenario_actual)

            # Calcular resultado
            if st.button("🚰 Calcular Riego Recomendado", key="calculate_single"):
                with st.spinner("Calculando recomendación..."):
                    resultado = run_simulation_custom(escenario_actual)

                if resultado:
                    st.success("✅ **Recomendación Calculada**")

                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.metric("⏱️ Tiempo de Riego", f"{resultado['tiempo_min']:.1f} min")
                    with col_b:
                        st.metric("🔄 Frecuencia Diaria", f"{resultado['frecuencia']:.2f} x/día")

                    # Interpretación
                    tiempo_rec = resultado['tiempo_min']
                    if tiempo_rec < 10:
                        st.info("💧 **Riego ligero recomendado** - Condiciones favorables")
                    elif tiempo_rec < 20:
                        st.info("⚖️ **Riego moderado recomendado** - Condiciones normales")
                    elif tiempo_rec < 35:
                        st.warning("💦 **Riego abundante recomendado** - Condiciones demandantes")
                    else:
                        st.error("🚨 **Riego urgente recomendado** - Condiciones críticas")

                    # Recomendaciones específicas
                    with st.expander("💡 Recomendaciones Específicas"):
                        st.markdown(f"""
                        **Planta:** {escenario_actual['planta']}
                        **Condiciones ambientales:** T={escenario_actual['temperatura']}°C, H={escenario_actual['humedad_suelo']}%, V={escenario_actual['viento']}km/h

                        **Interpretación del resultado:**
                        - Tiempo calculado: **{resultado['tiempo_min']:.1f} minutos**
                        - Frecuencia: **{resultado['frecuencia']:.2f} veces por día**
                        - **Recomendación:** {'Regar inmediatamente' if tiempo_rec > 25 else 'Monitorear condiciones' if tiempo_rec > 15 else 'Condiciones óptimas'}
                        """)

        st.divider()

        # Simulación masiva
        st.subheader("🔬 Simulación Comparativa")
        col1, col2 = st.columns([1, 1])

        with col1:
            st.markdown("**📊 Ejecutar Todos los Escenarios Predefinidos**")
            st.markdown("Compara cómo responde el sistema ante diferentes condiciones ambientales.")

            if st.button("🎯 Ejecutar Simulación Completa", key="run_all_scenarios"):
                with st.spinner("Simulando todos los escenarios..."):
                    rows = []
                    for nombre_sc, escenario_data in ESCENARIOS.items():
                        resultado = run_simulation_custom(escenario_data)
                        if resultado:
                            rows.append({
                                "Escenario": nombre_sc,
                                "Planta": escenario_data["planta"],
                                "Temp(°C)": escenario_data["temperatura"],
                                "HumSuelo(%)": escenario_data["humedad_suelo"],
                                "Tiempo(min)": ".1f",
                                "Frecuencia": ".2f",
                                "Prioridad": "Alta" if resultado['tiempo_min'] > 25 else "Media" if resultado['tiempo_min'] > 15 else "Baja"
                            })

                    if rows:
                        df_resultados = pd.DataFrame(rows)
                        st.success("✅ **Simulación completada exitosamente**")

                        # Mostrar tabla ordenada
                        st.dataframe(df_resultados.sort_values("Tiempo(min)", ascending=False), use_container_width=True)

                        # Estadísticas resumen
                        st.markdown("#### 📊 Resumen Estadístico")
                        col_stats1, col_stats2, col_stats3 = st.columns(3)
                        with col_stats1:
                            st.metric("Promedio Tiempo", ".1f")
                        with col_stats2:
                            st.metric("Máximo Tiempo", ".1f")
                        with col_stats3:
                            st.metric("Escenarios Simulados", len(rows))
                    else:
                        st.error("❌ Error en la simulación")

        with col2:
            st.markdown("**🎲 Modo Desafío Interactivo**")
            st.markdown("¡Pon a prueba tu intuición agrícola!")

            if "current_challenge" not in st.session_state:
                st.session_state.current_challenge = random.choice(list(ESCENARIOS.items())) if ESCENARIOS else None

            if st.button("🎯 Nuevo Desafío", key="new_challenge"):
                st.session_state.current_challenge = random.choice(list(ESCENARIOS.items())) if ESCENARIOS else None

            challenge = st.session_state.get("current_challenge")
            if challenge:
                nombre_ch, data_ch = challenge

                # Mostrar condiciones sin la respuesta
                st.markdown(f"**Escenario:** {nombre_ch}")
                condiciones_display = {
                    "🌡️ Temperatura": f"{data_ch['temperatura']} °C",
                    "💧 Humedad del suelo": ".0f",
                    "🌧️ Probabilidad de lluvia": ".0f",
                    "💨 Humedad del aire": ".0f",
                    "🌪️ Velocidad del viento": ".0f",
                    "🌱 Planta": data_ch.get("planta", "Tomate")
                }
                st.json(condiciones_display)

                # Input del usuario
                st.markdown("**Tu estimación:**")
                user_guess = st.slider("¿Cuántos minutos de riego recomendarías?", 0.0, 60.0, 15.0, key="user_guess")

                if st.button("🔥 Revelar Resultado", key="reveal_challenge"):
                    with st.spinner("Calculando..."):
                        real_result = run_simulation_custom(data_ch)

                    if real_result:
                        real_time = real_result['tiempo_min']
                        diferencia = abs(real_time - user_guess)

                        if diferencia < 5:
                            st.success(f"🎉 **¡Excelente intuición!** Diferencia: {diferencia:.1f} min")
                            st.balloons()
                        elif diferencia < 10:
                            st.info(f"👍 **Buen estimación!** Diferencia: {diferencia:.1f} min")
                        else:
                            st.warning(f"🤔 **Estimación conservadora** Diferencia: {diferencia:.1f} min")

                        col_res1, col_res2 = st.columns(2)
                        with col_res1:
                            st.metric("Tu Estimación", f"{user_guess:.1f} min")
                        with col_res2:
                            st.metric("Sistema Recomienda", ".1f")
                    else:
                        st.error("❌ Error en el cálculo del desafío")
            else:
                st.info("🎯 Haz clic en 'Nuevo Desafío' para comenzar")

        st.divider()

        # Información adicional
        st.subheader("📖 Información del Sistema de Simulación")
        with st.expander("ℹ️ Cómo funciona la simulación"):
            st.markdown("""
            **Simulador de Escenarios** permite probar el sistema de riego inteligente bajo diferentes condiciones:

            **👆 Escenario Individual:**
            - Selecciona un escenario predefinido o configura uno personalizado
            - Observa la respuesta del sistema ante condiciones específicas
            - Recibe recomendaciones interpretadas automáticamente

            **🔬 Simulación Comparativa:**
            - Ejecuta simulaciones para todos los escenarios predefinidos simultáneamente
            - Compara el rendimiento del sistema ante diferentes condiciones
            - Obtiene estadísticas resumen del comportamiento general

            **🎲 Modo Desafío:**
            - Prueba tus conocimientos intuitivos de riego agrícola
            - Compite contra el sistema experto
            - Aprende mediante la comparación con recomendaciones óptimas

            **Beneficios:**
            - 🧠 Aprende cómo funcionan las variables ambientales
            - 🎯 Mejora la toma de decisiones agricultura
            - 📊 Entiende la lógica difusa en acción
            """)

    except Exception as e:
        st.error(f"❌ Error en el simulador: {e}")
        import traceback
        st.code(f"Traceback completo:\n{traceback.format_exc()}")
