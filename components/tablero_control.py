from __future__ import annotations
import time
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
    """Gauge de nivel de confianza en porcentaje (0..100).

    Espera `confianza` en rango 0..1 y muestra 0..100 con 1 decimal.
    """
    pct = float(confianza) * 100.0
    color = "red" if pct < 40.0 else "yellow" if pct < 70.0 else "green"
    return go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=pct,
            title={"text": "Confianza"},
            domain={'x': [0, 1], 'y': [0, 1]},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': color},
                'steps': [
                    {'range': [0, 40], 'color': "lightcoral"},
                    {'range': [40, 70], 'color': "lightyellow"},
                    {'range': [70, 100], 'color': "lightgreen"}
                ],
            },
            number={'valueformat': '.1f', 'suffix': '%'}
        )
    )

def render_dashboard() -> None:
    st.title("🌊 Calculadora de Riego Inteligente")

    # Selector de clima integrado en la sección de la calculadora (manual por defecto)
    try:
        from components.weather_selector import render_weather_selector

        render_weather_selector()

        # Usar solo Streamlit (Python) para mostrar notificaciones.
        # Mostrar y limpiar flags para evitar repetición.
        if st.session_state.get('ws_applied'):
            st.success("✅ Valores aplicados a los sliders de la Calculadora")
            st.session_state.pop('ws_applied', None)
            st.session_state.pop('ws_applied_ts', None)

        if st.session_state.get('ws_updated'):
            st.info("🔁 Datos actualizados")
            st.session_state.pop('ws_updated', None)
            st.session_state.pop('ws_updated_ts', None)
    except Exception:
        # No mostramos un mensaje UI cuando el selector falla; solo limpiamos payload temporal
        st.session_state.pop('ws_last_payload', None)
        st.session_state.pop('ws_last_dept', None)
        st.session_state.pop('ws_last_latlon', None)

    with st.expander("¿Qué es Lógica Difusa?", expanded=False):
        st.write(
            "La lógica difusa permite razonar con valores imprecisos como 'alto' o 'bajo'. "
            "Este sistema usa inferencia de Mamdani y centroide para decidir tiempo y frecuencia de riego."
        )

    # Valores por defecto desde session_state['weather_inputs'] si están presentes
    ws = st.session_state.get('weather_inputs', {})
    defaults = {
        'temperature': 25.0,
        'soil_humidity': 30.0,
        'rain_probability': 10.0,
        'air_humidity': 40.0,
        'wind_speed': 8.0,
    }
    defaults.update({
        'temperature': ws.get('temperature', defaults['temperature']),
        'soil_humidity': ws.get('soil_humidity', defaults['soil_humidity']),
        'rain_probability': ws.get('rain_probability', defaults['rain_probability']),
        'air_humidity': ws.get('air_humidity', defaults['air_humidity']),
        'wind_speed': ws.get('wind_speed', defaults['wind_speed']),
    })

    # Inicializar session_state SOLO si no existen las keys (evita el warning de Streamlit)
    if 'calc_temp' not in st.session_state:
        st.session_state['calc_temp'] = defaults['temperature']
    if 'calc_soil' not in st.session_state:
        st.session_state['calc_soil'] = defaults['soil_humidity']
    if 'calc_rain' not in st.session_state:
        st.session_state['calc_rain'] = defaults['rain_probability']
    if 'calc_hum' not in st.session_state:
        st.session_state['calc_hum'] = defaults['air_humidity']
    if 'calc_wind' not in st.session_state:
        st.session_state['calc_wind'] = defaults['wind_speed']

    cols = st.columns(3)
    with cols[0]:
        temperatura = st.slider(
            "Temperatura (°C)", 0.0, 45.0,
            help="0-45°C",
            key="calc_temp",
        )
        humedad_suelo = st.slider(
            "Humedad del Suelo (%)", 0.0, 100.0,
            key="calc_soil",
        )
    with cols[1]:
        prob_lluvia = st.slider(
            "Probabilidad de Lluvia (%)", 0.0, 100.0,
            key="calc_rain",
        )
        humedad_ambiental = st.slider(
            "Humedad Ambiental (%)", 0.0, 100.0,
            key="calc_hum",
        )
    with cols[2]:
        viento = st.slider(
            "Velocidad del Viento (km/h)", 0.0, 50.0,
            key="calc_wind",
        )
        # Si hay recomendaciones de planta por departamento, mostrarlas primero
        rec = st.session_state.get('dept_recommended_plants')
        if rec:
            st.caption(f"Recomendados para {st.session_state.get('ws_department_main', '')}: {', '.join(rec)}")
            planta = st.selectbox("Tipo de planta", rec, index=0, key="calc_plant")
        else:
            planta = st.selectbox("Tipo de planta", PLANTS, index=0, key="calc_plant")
        auto = st.checkbox("Simulación Automática", value=False, key="calc_auto")

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

        # Calcular confianza usando método peak-weighted (da más peso al pico de activación)
        def peak_weighted_confidence(activations: dict, w_max: float = 0.7, alpha: float = 0.85) -> float:
            """
            Calcula confianza basada en activaciones de reglas fuzzy.
            - w_max: peso para el máximo (default 0.7 = 70% peso al pico)
            - alpha: exponente que controla penalización (< 1 = menos estricto)
            
            Valores típicos de confianza:
            - >0.65: Alta confianza (condiciones claras)
            - 0.45-0.65: Confianza media (condiciones normales)
            - <0.45: Baja confianza (condiciones ambiguas)
            """
            if not activations:
                return 0.75  # Default alto si no hay datos
            
            vals = list(activations.values())
            if not vals:
                return 0.75
            
            max_a = max(vals)
            mean_a = sum(vals) / len(vals)
            
            # Fórmula ajustada: más tolerante con activaciones moderadas
            # El alpha < 1 hace que valores medios (0.4-0.6) no se penalicen tanto
            conf = w_max * (max_a ** alpha) + (1.0 - w_max) * (mean_a ** alpha)
            
            # Boost adicional si hay múltiples reglas con activación razonable (>0.3)
            strong_rules = sum(1 for v in vals if v > 0.3)
            if strong_rules >= 3:
                conf = min(1.0, conf * 1.15)  # Bonus del 15% si hay consenso
            
            return min(1.0, float(conf))

        confianza = peak_weighted_confidence(act, w_max=0.7, alpha=0.85)

        # Mostrar alerta solo si la confianza es REALMENTE baja
        if confianza < 0.45:
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
            # Mostrar confianza como porcentaje con 1 decimal (ej. 81.0%)
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

        # Guardar configuración para compartir con visualizaciones
        st.session_state['calculadora_current'] = {
            'temperature': temperatura,
            'soil_humidity': humedad_suelo,
            'rain_probability': prob_lluvia,
            'air_humidity': humedad_ambiental,
            'wind_speed': viento,
            'planta': planta
        }

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

        # 🔍 TRAZABILIDAD COMPLETA
        show_traceability_explanation(
            inputs={
                'temperature': temperatura,
                'soil_humidity': humedad_suelo,
                'rain_probability': prob_lluvia,
                'air_humidity': humedad_ambiental,
                'wind_speed': viento
            },
            outputs={'tiempo': t, 'frecuencia': f},
            activaciones=act
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


def show_traceability_explanation(inputs: dict, outputs: dict, activaciones: dict) -> None:
    """Componente visual de trazabilidad completa de la decisión del sistema.

    Args:
        inputs: Diccionario con valores de entrada (temperature, soil_humidity, etc.)
        outputs: Diccionario con valores de salida (tiempo, frecuencia)
        activaciones: Diccionario con activación de reglas fuzzy
    """
    with st.expander("🔍 TRAZABILIDAD COMPLETA - ¿Por qué decidió así?", expanded=False):

        # Generar explicación trazable completa
        explicacion_completa = _engine.explain_decision_traceable(
            tiempo=outputs['tiempo'],
            frecuencia=outputs['frecuencia'],
            activaciones=activaciones,
            inputs=inputs
        )

        # Mostrar explicación en formato Markdown
        st.markdown(explicacion_completa)

        # Visualización adicional: Diagrama de reglas activas
        st.markdown("---")
        st.markdown("### 📊 Visualización de Reglas Activas")

        # Preparar datos para el gráfico
        top_rules = sorted(activaciones.items(), key=lambda x: x[1], reverse=True)[:8]

        if top_rules:
            # Crear gráfico de barras horizontales
            fig = go.Figure()

            # Barras principales
            fig.add_trace(go.Bar(
                y=[f"{regla} ({act:.2f})" for regla, act in top_rules],
                x=[act for regla, act in top_rules],
                orientation='h',
                marker=dict(
                    color=[act for regla, act in top_rules],
                    colorscale=[
                        [0.0, '#e3f2fd'],  # Azul muy claro
                        [0.3, '#2196f3'],  # Azul
                        [0.7, '#ff9800'],  # Naranja
                        [1.0, '#f44336']   # Rojo
                    ],
                    showscale=True,
                    colorbar=dict(
                        title="Activación",
                        titleside="right",
                        tickformat=".2f"
                    )
                ),
                text=[f"{act:.3f}" for regla, act in top_rules],
                textposition='outside',
                hovertemplate="<b>%{y}</b><br>Activación: %{x:.3f}<extra></extra>"
            ))

            # Configurar layout
            fig.update_layout(
                title="Top 8 Reglas Más Activas",
                xaxis=dict(
                    title="Nivel de Activación (0-1)",
                    range=[0, 1.1],
                    tickformat=".2f"
                ),
                yaxis=dict(
                    title="Regla Fuzzy",
                    autorange="reversed"  # Para que la más activa aparezca arriba
                ),
                height=max(400, len(top_rules) * 40),
                margin=dict(l=200, r=100, t=50, b=50),
                template="plotly_white"
            )

            st.plotly_chart(fig, use_container_width=True)

            # Información adicional
            st.markdown("---")
            col1, col2, col3 = st.columns(3)

            with col1:
                max_activacion = max(activaciones.values())
                regla_max = max(activaciones.items(), key=lambda x: x[1])[0]
                st.metric(
                    "🔥 Regla Más Activa",
                    regla_max,
                    f"{max_activacion:.3f}"
                )

            with col2:
                reglas_activas = sum(1 for act in activaciones.values() if act > 0.1)
                st.metric(
                    "📋 Reglas Activas",
                    f"{reglas_activas}/33",
                    f"{reglas_activas/33*100:.0f}%"
                )

            with col3:
                # Calcular diversidad de activación
                valores = list(activaciones.values())
                diversidad = len([v for v in valores if v > 0.2]) / len(valores)
                st.metric(
                    "🎭 Diversidad",
                    f"{diversidad:.1f}",
                    help="Proporción de reglas con activación significativa"
                )

        # Consejos de interpretación
        st.markdown("---")
        st.markdown("### 💡 Cómo Interpretar Esta Trazabilidad")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("""
            **🎯 Activación Alta (0.7-1.0):**
            - Regla muy influyente en la decisión
            - Condición se cumple fuertemente
            - Confianza alta en esta regla

            **📊 Activación Media (0.3-0.7):**
            - Regla moderadamente activa
            - Contribuye parcialmente a la decisión
            - Considerar junto con otras reglas
            """)

        with col2:
            st.markdown("""
            **📋 Activación Baja (0.0-0.3):**
            - Regla poco relevante
            - Condición no se cumple
            - Mínimo impacto en decisión final

            **🔍 Variables Críticas:**
            - Aquellas marcadas con 🚨 o 🔥
            - Tienen mayor impacto en el resultado
            - Monitorear especialmente
            """)

        # Nota final
        st.info("""
        **💡 Recordatorio:** Esta trazabilidad muestra exactamente cómo el sistema de lógica difusa 
        procesa tus condiciones ambientales para tomar decisiones de riego. Cada regla representa 
        conocimiento experto agrícola traducido a lógica matemática.
        """)
