from __future__ import annotations
import json
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple
import pandas as pd

DATA_DIR = "data"
HISTORY_CSV = os.path.join(DATA_DIR, "history.csv")
HISTORY_JSONL = os.path.join(DATA_DIR, "history.jsonl")
PLANTS_JSON = os.path.join(DATA_DIR, "plantas.json")
SCENARIOS_JSON = os.path.join(DATA_DIR, "escenarios_prueba.json")


def ensure_data_files() -> None:
    """Ensure required data directories/files exist with defaults."""
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(HISTORY_CSV):
        pd.DataFrame(
            columns=[
                "ts",
                "temperatura",
                "humedad_suelo",
                "prob_lluvia",
                "humedad_ambiental",
                "viento",
                "planta",
                "tiempo_min",
                "frecuencia",
            ]
        ).to_csv(HISTORY_CSV, index=False)
    if not os.path.exists(HISTORY_JSONL):
        with open(HISTORY_JSONL, "w", encoding="utf-8") as f:
            f.write("")


def validate_inputs(
    temperature: float,
    soil_humidity: float,
    rain_probability: float,
    air_humidity: float,
    wind_speed: float,
) -> None:
    """Validate user inputs ranges.

    Raises:
        ValueError: if any value is out of the specified ranges.
    """
    if not (0 <= temperature <= 45):
        raise ValueError("La temperatura debe estar entre 0 y 45 °C")
    if not (0 <= soil_humidity <= 100):
        raise ValueError("La humedad del suelo debe estar entre 0 y 100 %")
    if not (0 <= rain_probability <= 100):
        raise ValueError("La probabilidad de lluvia debe estar entre 0 y 100 %")
    if not (0 <= air_humidity <= 100):
        raise ValueError("La humedad ambiental debe estar entre 0 y 100 %")
    if not (0 <= wind_speed <= 50):
        raise ValueError("La velocidad del viento debe estar entre 0 y 50 km/h")


def save_history(record: Dict[str, Any]) -> None:
    """Append a decision record to history files."""
    ensure_data_files()
    # CSV
    df = pd.DataFrame([record])
    if os.path.exists(HISTORY_CSV):
        df.to_csv(HISTORY_CSV, mode="a", header=False, index=False)
    else:
        df.to_csv(HISTORY_CSV, index=False)
    # JSONL
    with open(HISTORY_JSONL, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def load_history() -> pd.DataFrame:
    """Load the history as a DataFrame."""
    ensure_data_files()
    try:
        return pd.read_csv(HISTORY_CSV)
    except Exception:
        return pd.DataFrame()


def export_history_csv(path: str) -> None:
    """Export history to a CSV file path."""
    df = load_history()
    df.to_csv(path, index=False)


def timestamp() -> int:
    """Return current unix timestamp (seconds)."""
    return int(time.time())


def clear_history() -> None:
    """Clear history CSV and JSONL files and recreate headers."""
    os.makedirs(DATA_DIR, exist_ok=True)
    # reset CSV
    pd.DataFrame(
        columns=[
            "ts",
            "temperatura",
            "humedad_suelo",
            "prob_lluvia",
            "humedad_ambiental",
            "viento",
            "planta",
            "tiempo_min",
            "frecuencia",
        ]
    ).to_csv(HISTORY_CSV, index=False)
    # reset JSONL
    with open(HISTORY_JSONL, "w", encoding="utf-8") as f:
        f.write("")


def estimate_water_saving(tiempo_min: float, frecuencia: float) -> float:
    """Heurística simple para estimar ahorro de agua (L/semana).

    Supone riego base 60 min x 3/día -> 1.0 factor; ahorro relativo vs base.
    """
    base = 60.0 * 3.0
    actual = max(0.0, min(60.0, float(tiempo_min))) * max(0.0, min(4.0, float(frecuencia)))
    ahorro_rel = max(0.0, (base - actual) / base)
    # Escalar a litros/semana (ej. 100 L como base de referencia diaria)
    litros_dia_base = 100.0
    return round(ahorro_rel * litros_dia_base * 7.0, 1)
