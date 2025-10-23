from __future__ import annotations
from typing import Dict, Any, List
import json
import os

PLANT_KB: Dict[str, Dict[str, Any]] = {
    "Tomate": {
        "humedad_suelo_opt": [50, 80],
        "temperatura_opt": [18, 30],
        "factor_ajuste": 1.0,
        "tolerancia_extremos": "media",
        "consejos": "Evitar encharcamientos; riego frecuente en calor alto.",
    },
    "Lechuga": {
        "humedad_suelo_opt": [60, 85],
        "temperatura_opt": [10, 24],
        "factor_ajuste": 0.9,
        "tolerancia_extremos": "baja",
        "consejos": "Prefiere suelo siempre húmedo; sensible al calor.",
    },
    "Zanahoria": {
        "humedad_suelo_opt": [45, 75],
        "temperatura_opt": [10, 25],
        "factor_ajuste": 0.95,
        "tolerancia_extremos": "media",
        "consejos": "Riegos regulares; evitar suelos muy compactos.",
    },
    "Cactus": {
        "humedad_suelo_opt": [10, 30],
        "temperatura_opt": [20, 40],
        "factor_ajuste": 0.4,
        "tolerancia_extremos": "alta",
        "consejos": "Riego muy espaciado; excelente drenaje.",
    },
    "Rosa": {
        "humedad_suelo_opt": [40, 70],
        "temperatura_opt": [15, 28],
        "factor_ajuste": 1.0,
        "tolerancia_extremos": "media",
        "consejos": "Riegos profundos; evitar mojar hojas en exceso.",
    },
    "Césped": {
        "humedad_suelo_opt": [50, 80],
        "temperatura_opt": [15, 28],
        "factor_ajuste": 1.1,
        "tolerancia_extremos": "media",
        "consejos": "Frecuencia moderada; más en verano.",
    },
    "Maíz": {
        "humedad_suelo_opt": [40, 70],
        "temperatura_opt": [18, 32],
        "factor_ajuste": 1.05,
        "tolerancia_extremos": "media",
        "consejos": "Aumentar riego en floración y llenado de grano.",
    },
    "Fresa": {
        "humedad_suelo_opt": [60, 85],
        "temperatura_opt": [15, 26],
        "factor_ajuste": 1.0,
        "tolerancia_extremos": "baja",
        "consejos": "Evitar encharcar; riego frecuente y ligero.",
    },
}

PLANTS = list(PLANT_KB.keys())


HISTORICO_PATH = os.path.join("data", "historico.json")


def _load_historico() -> List[Dict[str, Any]]:
    try:
        if os.path.exists(HISTORICO_PATH):
            with open(HISTORICO_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return []


def _save_historico(registros: List[Dict[str, Any]]) -> None:
    try:
        os.makedirs(os.path.dirname(HISTORICO_PATH), exist_ok=True)
        with open(HISTORICO_PATH, "w", encoding="utf-8") as f:
            json.dump(registros[-100:], f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def get_recomendacion(planta: str, condiciones: Dict[str, float], decision: Dict[str, float]) -> Dict[str, Any]:
    """Ajusta la recomendación según KB y guarda en historico.json (últimos 100).

    condiciones: {temperatura, humedad_suelo, prob_lluvia, humedad_ambiente, velocidad_viento}
    decision: {tiempo_min, frecuencia}
    """
    kb = PLANT_KB.get(planta, {})
    factor = float(kb.get("factor_ajuste", 1.0))
    tiempo_aj = float(decision.get("tiempo_min", 0)) * factor
    # Heurística simple: si humedad_suelo está por encima del óptimo, reducir 20%
    hs = float(condiciones.get("humedad_suelo", 0))
    opt = kb.get("humedad_suelo_opt", [0, 100])
    if hs > opt[1]:
        tiempo_aj *= 0.8
    if hs < opt[0]:
        tiempo_aj *= 1.1

    out = {
        "planta": planta,
        "tiempo_ajustado": max(0.0, min(60.0, tiempo_aj)),
        "frecuencia": float(decision.get("frecuencia", 0)),
        "consejos": kb.get("consejos", ""),
    }

    # Guardar en historico.json (mantener 100)
    registros = _load_historico()
    registros.append({
        **condiciones,
        "planta": planta,
        "tiempo_min": round(out["tiempo_ajustado"], 2),
        "frecuencia": round(out["frecuencia"], 2),
    })
    _save_historico(registros)
    return out
