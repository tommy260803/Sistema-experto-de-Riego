import pytest
import pandas as pd
from src.fuzzy_engine import FuzzyIrrigationSystem
from src.knowledge_base import PLANT_KB, get_recomendacion


def test_flujo_completo():
    sys = FuzzyIrrigationSystem()
    inputs = dict(temperatura=26, humedad_suelo=40, prob_lluvia=20, humedad_ambiente=50, velocidad_viento=12)
    t, f, act = sys.calculate_irrigation(
        temperature=inputs['temperatura'],
        soil_humidity=inputs['humedad_suelo'],
        rain_probability=inputs['prob_lluvia'],
        air_humidity=inputs['humedad_ambiente'],
        wind_speed=inputs['velocidad_viento'],
    )
    reco = get_recomendacion("Tomate", inputs, {"tiempo_min": t, "frecuencia": f})
    assert 0 <= reco["tiempo_ajustado"] <= 60


def test_todas_plantas():
    sys = FuzzyIrrigationSystem()
    for plant in PLANT_KB.keys():
        t, f, act = sys.calculate_irrigation(temperature=24, soil_humidity=55, rain_probability=30, air_humidity=60, wind_speed=10)
        reco = get_recomendacion(plant, {"temperatura":24, "humedad_suelo":55, "prob_lluvia":30, "humedad_ambiente":60, "velocidad_viento":10}, {"tiempo_min": t, "frecuencia": f})
        assert isinstance(reco, dict)
