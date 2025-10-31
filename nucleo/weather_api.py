"""Cliente simple para Open-Meteo con cache en memoria y TTL.

Provee:
- get_weather(lat, lon, ttl=300) -> dict con temperatura, humedad, prob_lluvia, viento, soil_moisture
- invalidate_cache(lat=None, lon=None) -> invalida una entrada o toda la cache

Notas / supuestos:
- Usamos el endpoint público de Open-Meteo (no requiere API key).
- Para humedad y probabilidad de lluvia usamos datos horarios y tomamos el valor horario más cercano a la hora actual.
- Estimación heurística de humedad del suelo: combinación simple basada en humedad ambiental, probabilidad de lluvia y temperatura.
"""
from __future__ import annotations
import time
import math
from typing import Dict, Tuple
import requests

_CACHE: Dict[Tuple[float, float], Dict] = {}


def _now_ts() -> float:
    return time.time()


def invalidate_cache(lat: float | None = None, lon: float | None = None) -> None:
    """Invalidar cache: si lat/lon son None invalida todo; si se pasan valores invalida esa key."""
    if lat is None or lon is None:
        _CACHE.clear()
        return
    key = (float(lat), float(lon))
    _CACHE.pop(key, None)


def _heuristic_soil_moisture(temp_c: float, humidity: float, rain_prob: float) -> float:
    """Estimación heurística de humedad de suelo (0..100).

    Nueva fórmula (más conservadora y teniendo en cuenta viento y efecto de temperatura):
    - Base inicial moderada (30).
    - La humedad ambiental aporta hasta 0.35*humidity.
    - La probabilidad de lluvia aporta hasta 0.40*rain_prob.
    - Temperaturas por encima de 20°C reducen humedad (factor 0.25 por grado sobre 20°C).
    - El viento reduce la humedad del suelo ligeramente (factor 0.15 * viento).

    La fórmula es heurística, sirve para rellenar el input cuando no hay sensor de suelo.
    """
    base = 30.0
    base += 0.35 * humidity
    base += 0.40 * rain_prob
    # penalizar temperaturas altas (solo la porción sobre 20°C)
    temp_penalty = 0.25 * max(0.0, (temp_c - 20.0))
    base -= temp_penalty
    # viento reduce humedad del suelo
    # si no viene el dato de viento, asumimos 0
    try:
        wind = float(globals().get('last_wind_speed', 0.0))
    except Exception:
        wind = 0.0
    base -= 0.15 * wind

    val = max(0.0, min(100.0, base))
    return round(val, 1)


def get_weather(lat: float, lon: float, ttl: int = 300) -> Dict:
    """Devuelve un dict con keys: temperature, humidity, rain_probability, wind_speed, soil_moisture, time, lat, lon

    Cachea resultados en memoria por (lat, lon) durante `ttl` segundos.
    """
    key = (float(lat), float(lon))
    now = _now_ts()
    cached = _CACHE.get(key)
    if cached and now - cached.get("ts", 0) < ttl:
        return dict(cached.get("data", {}), _cached=True)

    # Construir URL Open-Meteo
    # Solicitamos hourly para variables que no siempre están en current_weather
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        "&hourly=temperature_2m,relativehumidity_2m,precipitation_probability,windspeed_10m"
        "&current_weather=true"
        "&timezone=auto"
    )

    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        payload = resp.json()

        # Preferir current_weather para temperatura y viento
        current = payload.get("current_weather") or {}
        temp = current.get("temperature")
        wind = current.get("windspeed")

        # Para humedad y prob_lluvia buscaremos el índice horario más cercano
        humidity = None
        rain_prob = None
        time_idx = None
        hourly = payload.get("hourly", {})
        times = hourly.get("time", [])
        if times:
            # elegir el índice 0 (hora actual reportada por la API) si existe
            time_idx = 0
            hums = hourly.get("relativehumidity_2m", [])
            rains = hourly.get("precipitation_probability", [])
            winds = hourly.get("windspeed_10m", [])
            if hums and len(hums) > time_idx:
                humidity = hums[time_idx]
            if rains and len(rains) > time_idx:
                rain_prob = rains[time_idx]
            if wind is None and winds and len(winds) > time_idx:
                wind = winds[time_idx]

        # Fallbacks
        temp = float(temp) if temp is not None else None
        wind = float(wind) if wind is not None else 0.0
        humidity = float(humidity) if humidity is not None else 50.0
        rain_prob = float(rain_prob) if rain_prob is not None else 0.0

        soil = _heuristic_soil_moisture(temp or 25.0, humidity, rain_prob)

        data = {
            "temperature": round(temp, 1) if temp is not None else None,
            "humidity": round(humidity, 1),
            "rain_probability": round(rain_prob, 1),
            "wind_speed": round(wind, 1),
            "soil_moisture_est": soil,
            "time": payload.get("generationtime_ms") if payload else None,
            "lat": lat,
            "lon": lon,
        }

        _CACHE[key] = {"ts": now, "data": data}
        return dict(data, _cached=False)
    except Exception as e:
        # En caso de fallo devolvemos valores razonables por defecto y no rompemos la app
        fallback = {
            "temperature": 25.0,
            "humidity": 50.0,
            "rain_probability": 0.0,
            "wind_speed": 5.0,
            "soil_moisture_est": _heuristic_soil_moisture(25.0, 50.0, 0.0),
            "time": None,
            "lat": lat,
            "lon": lon,
        }
        return dict(fallback, _error=str(e))
