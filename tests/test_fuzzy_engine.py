import pytest
from nucleo.motor_difuso import FuzzyIrrigationSystem


def test_calcular_riego_seco():
    sys = FuzzyIrrigationSystem()
    t, f, act = sys.calculate_irrigation(
        temperature=35, soil_humidity=10, rain_probability=5, air_humidity=30, wind_speed=10
    )
    assert 0 <= t <= 60
    assert 0 <= f <= 4
    # suelo seco debería activar reglas que empujen a tiempos mayores
    assert t >= 15


def test_calcular_riego_humedo():
    sys = FuzzyIrrigationSystem()
    t, f, act = sys.calculate_irrigation(
        temperature=20, soil_humidity=85, rain_probability=40, air_humidity=70, wind_speed=8
    )
    assert 0 <= t <= 60
    assert t <= 20


def test_reglas_coherencia():
    sys = FuzzyIrrigationSystem()
    _, _, act = sys.calculate_irrigation(
        temperature=28, soil_humidity=35, rain_probability=20, air_humidity=45, wind_speed=12
    )
    # no activaciones negativas ni >1
    for v in act.values():
        assert 0.0 <= v <= 1.0


def test_rango_salidas():
    sys = FuzzyIrrigationSystem()
    for temp in [0, 25, 50]:
        t, f, _ = sys.calculate_irrigation(
            temperature=temp, soil_humidity=50, rain_probability=50, air_humidity=50, wind_speed=10
        )
        assert 0 <= t <= 60
        assert 0 <= f <= 4
