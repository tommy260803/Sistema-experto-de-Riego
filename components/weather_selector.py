
from __future__ import annotations
import time
from typing import Dict, Tuple

import streamlit as st

from nucleo import weather_api
from nucleo.base_conocimientos import PLANTS


# Mapeo de departamentos del Perú -> (Región, lat, lon)
# Coordenadas aproximadas (capital o centro departamental)
DEPARTMENTS: Dict[str, Tuple[str, float, float]] = {
    'Lima': ('Costa', -12.0464, -77.0428),
    'Callao': ('Costa', -12.0568, -77.1161),
    'Arequipa': ('Sierra', -16.4090, -71.5375),
    'Cusco': ('Sierra', -13.5319, -71.9675),
    'Piura': ('Costa', -5.1945, -80.6328),
    'La Libertad': ('Costa', -8.1140, -79.0215),
    'Áncash': ('Sierra', -9.5260, -77.5288),
    'Ica': ('Costa', -14.0678, -75.7288),
    'Huancavelica': ('Sierra', -12.7825, -74.9770),
    'Junín': ('Sierra', -11.0211, -75.8970),
    'Ayacucho': ('Sierra', -13.1619, -74.2236),
    'Huánuco': ('Sierra', -9.9174, -76.2402),
    'San Martín': ('Selva', -6.4888, -76.3536),
    'Loreto': ('Selva', -3.7496, -73.2516),
    'Ucayali': ('Selva', -8.3790, -74.5530),
    'Puno': ('Sierra', -15.8402, -70.0219),
    'Tacna': ('Costa', -18.0146, -70.2470),
    'Tumbes': ('Costa', -3.5666, -80.4510),
    'Moquegua': ('Costa', -17.1935, -70.9319),
    'Apurímac': ('Sierra', -13.6364, -72.8795),
    'Cajamarca': ('Sierra', -7.1626, -78.5123),
    'Amazonas': ('Selva', -5.7000, -78.6667),
    'Madre de Dios': ('Selva', -12.5954, -69.1896),
    'Cusco Reg': ('Sierra', -13.5319, -71.9675),
}

# Mapear departamentos a cultivos/frutas/verduras comunes (nombres deben existir en data/plantas.json)
DEPARTMENT_CROPS: Dict[str, Tuple[str, ...]] = {
    'Lima': ('Tomate', 'Lechuga', 'Fresa', 'Papa', 'Cebolla'),
    'Callao': ('Tomate', 'Lechuga', 'Cebolla'),
    'Arequipa': ('Papa', 'Maíz', 'Tomate'),
    'Cusco': ('Papa', 'Maíz', 'Fresa'),
    'Piura': ('Mango', 'Tomate', 'Maíz'),
    'La Libertad': ('Tomate', 'Lechuga', 'Papa'),
    'Áncash': ('Papa', 'Tomate'),
    'Ica': ('Papa', 'Tomate', 'Fresa'),
    'Junín': ('Papa', 'Zanahoria', 'Maíz'),
    'Puno': ('Papa', 'Quinoa'),
    'Tacna': ('Tomate', 'Papa'),
    'Tumbes': ('Mango', 'Tomate'),
    'Moquegua': ('Papa', 'Tomate'),
    'Cajamarca': ('Papa', 'Maíz'),
    'San Martín': ('Maíz', 'Fresa'),
    'Loreto': ('Plátano', 'Yuca'),
    'Ucayali': ('Plátano', 'Yuca'),
    'Madre de Dios': ('Plátano', 'Yuca'),
}


def render_weather_selector() -> None:

    # Mostrar la opción para revelar las opciones de Open‑Meteo
    if st.button("Mostrar opciones Open‑Meteo", key="ws_show_options"):
        st.session_state['ws_show_openmeteo'] = True
        st.rerun()

    show_om = st.session_state.get('ws_show_openmeteo', False)

    st.markdown("**Modo Manual — Ajusta los valores usando los sliders de la Calculadora si no usas la API**")

    if not show_om:
        # nothing more to do in manual mode
        return

    st.markdown("---")
    st.subheader("Open‑Meteo")
    st.caption("Selecciona región y departamento para consultar datos reales vía Open‑Meteo.")

    # Región como selectbox
    region = st.selectbox("Región", ["Costa", "Sierra", "Selva"], index=0, key="ws_region_main")
    options = [d for d, v in DEPARTMENTS.items() if v[0] == region]
    if not options:
        st.info("No hay departamentos configurados para esta región")
        return

    dept = st.selectbox("Departamento", options, key="ws_department_main")
    reg, lat, lon = DEPARTMENTS.get(dept, (region, -12.0, -77.0))
    st.caption(f"Coordenadas: {lat:.4f}, {lon:.4f}")

    # Obtener automáticamente cuando cambia el departamento / coordenadas
    need_fetch = (
        'ws_last_payload' not in st.session_state
        or st.session_state.get('ws_last_dept') != dept
        or st.session_state.get('ws_last_latlon') != (lat, lon)
    )

    if need_fetch:
        try:
            payload = weather_api.get_weather(lat, lon)
            st.session_state['ws_last_payload'] = payload
            st.session_state['ws_last_dept'] = dept
            st.session_state['ws_last_latlon'] = (lat, lon)
        except Exception as e:
            st.error(f"Error consultando Open‑Meteo: {e}")

    payload = st.session_state.get('ws_last_payload')
    if not payload:
        return

    # Guardar y mostrar cultivos/frutas recomendadas para este departamento
    rec = list(DEPARTMENT_CROPS.get(dept, []))
    # Filtrar recomendaciones para que exista la planta en la base de conocimientos
    if rec:
        # construir mapa case-insensitive de PLANTS
        available = {p.lower(): p for p in PLANTS}
        rec_filtered = [available.get(x.lower()) for x in rec if x.lower() in available]
        rec_filtered = [r for r in rec_filtered if r]
        if rec_filtered:
            st.session_state['dept_recommended_plants'] = rec_filtered
            st.caption(f"Cultivos/verduras/frutas comunes en {dept}: {', '.join(rec_filtered)}")
        else:
            # si ninguna recomendación existe en KB, no imponer (limpiamos)
            st.session_state.pop('dept_recommended_plants', None)
    else:
        st.session_state.pop('dept_recommended_plants', None)

    st.markdown("**Valores devueltos por Open‑Meteo:**")

    def _fmt(v):
        try:
            if v is None:
                return "-"
            return f"{float(v):.2f}"
        except Exception:
            return str(v)

    show = {
        'Temperatura (°C)': _fmt(payload.get('temperature')),
        'Humedad (%)': _fmt(payload.get('humidity')),
        'Probabilidad Lluvia (%)': _fmt(payload.get('rain_probability')),
        'Viento (km/h)': _fmt(payload.get('wind_speed')),
        'Humedad Suelo Est. (%)': _fmt(payload.get('soil_moisture_est')),
    }
    st.table([show])

    # Botones: Aplicar Valores y Actualizar (no mostrar notificaciones directas aquí)
    c1, c2 = st.columns([2, 1])
    with c1:
        if st.button("Aplicar Valores", key="ws_apply_to_sliders", type="primary"):
            # aplicar a sliders existentes (keys calc_*)
            st.session_state['calc_temp'] = float(payload.get('temperature', st.session_state.get('calc_temp', 25.0)))
            st.session_state['calc_soil'] = float(payload.get('soil_moisture_est', st.session_state.get('calc_soil', 40.0)))
            st.session_state['calc_rain'] = float(payload.get('rain_probability', st.session_state.get('calc_rain', 10.0)))
            st.session_state['calc_hum'] = float(payload.get('humidity', st.session_state.get('calc_hum', 50.0)))
            st.session_state['calc_wind'] = float(payload.get('wind_speed', st.session_state.get('calc_wind', 5.0)))
            # guardar en weather_inputs
            st.session_state['weather_inputs'] = {
                'temperature': st.session_state['calc_temp'],
                'soil_humidity': st.session_state['calc_soil'],
                'rain_probability': st.session_state['calc_rain'],
                'air_humidity': st.session_state['calc_hum'],
                'wind_speed': st.session_state['calc_wind'],
                'location': {'department': dept, 'lat': lat, 'lon': lon},
                'fetched_auto': True,
            }
            st.session_state['ws_applied'] = True
            st.session_state['ws_applied_ts'] = time.time()

    with c2:
        if st.button("Actualizar", key="ws_refresh_main", type="secondary"):
            try:
                weather_api.invalidate_cache(lat, lon)
            except Exception:
                weather_api.invalidate_cache()
            try:
                payload = weather_api.get_weather(lat, lon)
                st.session_state['ws_last_payload'] = payload
                st.session_state['ws_updated'] = True
                st.session_state['ws_updated_ts'] = time.time()
            except Exception as e:
                st.error(f"Error actualizando: {e}")