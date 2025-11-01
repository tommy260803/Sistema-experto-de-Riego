import pytest
from nucleo.motor_difuso import FuzzyIrrigationSystem
from nucleo.utilidades import validate_inputs


def test_caso_borde_limites_rangos():
    """Caso borde - validar comportamiento en los límites exactos de los rangos."""
    sistema = FuzzyIrrigationSystem()

    # Valores en los límites exactos
    casos_limite = [
        # Temperatura límites
        {"temp": 0, "humedad": 50, "lluvia": 20, "aire": 60, "viento": 10, "desc": "Temp mínima"},
        {"temp": 50, "humedad": 50, "lluvia": 20, "aire": 60, "viento": 10, "desc": "Temp máxima"},

        # Humedad suelo límites
        {"temp": 25, "humedad": 0, "lluvia": 20, "aire": 60, "viento": 10, "desc": "Humedad suelo mínima"},
        {"temp": 25, "humedad": 100, "lluvia": 20, "aire": 60, "viento": 10, "desc": "Humedad suelo máxima"},

        # Lluvia límites
        {"temp": 25, "humedad": 50, "lluvia": 0, "aire": 60, "viento": 10, "desc": "Lluvia mínima"},
        {"temp": 25, "humedad": 50, "lluvia": 100, "aire": 60, "viento": 10, "desc": "Lluvia máxima"},

        # Humedad aire límites
        {"temp": 25, "humedad": 50, "lluvia": 20, "aire": 0, "viento": 10, "desc": "Humedad aire mínima"},
        {"temp": 25, "humedad": 50, "lluvia": 20, "aire": 100, "viento": 10, "desc": "Humedad aire máxima"},

        # Viento límites
        {"temp": 25, "humedad": 50, "lluvia": 20, "aire": 60, "viento": 0, "desc": "Viento mínimo"},
        {"temp": 25, "humedad": 50, "lluvia": 20, "aire": 60, "viento": 50, "desc": "Viento máximo"},
    ]

    for caso in casos_limite:
        tiempo, frecuencia, activaciones = sistema.calculate_irrigation(
            temperature=caso["temp"],
            soil_humidity=caso["humedad"],
            rain_probability=caso["lluvia"],
            air_humidity=caso["aire"],
            wind_speed=caso["viento"]
        )

        # Verificar rangos válidos
        assert 0 <= tiempo <= 60, f"Tiempo fuera de rango en {caso['desc']}: {tiempo}"
        assert 0.5 <= frecuencia <= 4, f"Frecuencia fuera de rango en {caso['desc']}: {frecuencia}"

        # Verificar que todas las activaciones están en rango
        for regla, activacion in activaciones.items():
            assert 0.0 <= activacion <= 1.0, f"Activación de {regla} fuera de rango en {caso['desc']}: {activacion}"


def test_caso_borde_combinaciones_extremas():
    """Caso borde - combinaciones de valores extremos que podrían causar problemas."""
    sistema = FuzzyIrrigationSystem()

    # Combinaciones extremas
    escenarios_extremos = [
        # Todo mínimo
        {"temp": 0, "humedad": 0, "lluvia": 0, "aire": 0, "viento": 0, "desc": "Todo mínimo"},
        # Todo máximo
        {"temp": 50, "humedad": 100, "lluvia": 100, "aire": 100, "viento": 50, "desc": "Todo máximo"},
        # Contradicciones
        {"temp": 50, "humedad": 0, "lluvia": 100, "aire": 0, "viento": 50, "desc": "Contradicción extrema"},
        {"temp": 0, "humedad": 100, "lluvia": 0, "aire": 100, "viento": 0, "desc": "Otra contradicción"},
    ]

    for escenario in escenarios_extremos:
        tiempo, frecuencia, activaciones = sistema.calculate_irrigation(
            temperature=escenario["temp"],
            soil_humidity=escenario["humedad"],
            rain_probability=escenario["lluvia"],
            air_humidity=escenario["aire"],
            wind_speed=escenario["viento"]
        )

        # Verificar que no hay valores problemáticos
        assert not (tiempo != tiempo), f"NaN detectado en tiempo: {escenario['desc']}"
        assert not (frecuencia != frecuencia), f"NaN detectado en frecuencia: {escenario['desc']}"

        # Verificar rangos válidos
        assert 0 <= tiempo <= 60, f"Tiempo fuera de rango en {escenario['desc']}: {tiempo}"
        assert 0.5 <= frecuencia <= 4, f"Frecuencia fuera de rango en {escenario['desc']}: {frecuencia}"

        # Verificar que al menos una regla se activa significativamente
        max_activacion = max(activaciones.values())
        assert max_activacion > 0.1, f"Ninguna regla se activa significativamente en {escenario['desc']}: {max_activacion}"


def test_caso_borde_validacion_entradas():
    """Caso borde - validar que el sistema rechaza entradas inválidas."""
    # Valores fuera de rango deberían lanzar ValueError

    # Temperatura fuera de rango
    with pytest.raises(ValueError, match="temperatura"):
        validate_inputs(-1, 50, 20, 60, 10)

    with pytest.raises(ValueError, match="temperatura"):
        validate_inputs(51, 50, 20, 60, 10)

    # Humedad suelo fuera de rango
    with pytest.raises(ValueError, match="humedad del suelo"):
        validate_inputs(25, -1, 20, 60, 10)

    with pytest.raises(ValueError, match="humedad del suelo"):
        validate_inputs(25, 101, 20, 60, 10)

    # Probabilidad lluvia fuera de rango
    with pytest.raises(ValueError, match="probabilidad de lluvia"):
        validate_inputs(25, 50, -1, 60, 10)

    with pytest.raises(ValueError, match="probabilidad de lluvia"):
        validate_inputs(25, 50, 101, 60, 10)

    # Humedad aire fuera de rango
    with pytest.raises(ValueError, match="humedad ambiental"):
        validate_inputs(25, 50, 20, -1, 10)

    with pytest.raises(ValueError, match="humedad ambiental"):
        validate_inputs(25, 50, 20, 101, 10)

    # Velocidad viento fuera de rango
    with pytest.raises(ValueError, match="velocidad del viento"):
        validate_inputs(25, 50, 20, 60, -1)

    with pytest.raises(ValueError, match="velocidad del viento"):
        validate_inputs(25, 50, 20, 60, 51)


def test_caso_borde_transiciones_suaves():
    """Caso borde - verificar que las transiciones entre conjuntos son suaves."""
    sistema = FuzzyIrrigationSystem()

    # Probar puntos cerca de las transiciones de temperatura
    puntos_transicion = [14.9, 15.0, 15.1, 19.9, 20.0, 20.1, 24.9, 25.0, 25.1, 29.9, 30.0, 30.1]

    resultados_anteriores = None

    for temp in puntos_transicion:
        tiempo, frecuencia, activaciones = sistema.calculate_irrigation(
            temperature=temp,
            soil_humidity=50,
            rain_probability=20,
            air_humidity=60,
            wind_speed=10
        )

        # Verificar que no hay saltos bruscos (cambios > 50% entre puntos consecutivos)
        if resultados_anteriores is not None:
            cambio_tiempo = abs(tiempo - resultados_anteriores[0]) / max(tiempo, resultados_anteriores[0], 1)
            cambio_frecuencia = abs(frecuencia - resultados_anteriores[1]) / max(frecuencia, resultados_anteriores[1], 0.1)

            assert cambio_tiempo < 0.5, f"Cambio brusco en tiempo entre {resultados_anteriores[2]}°C y {temp}°C: {cambio_tiempo:.2f}"
            assert cambio_frecuencia < 0.5, f"Cambio brusco en frecuencia entre {resultados_anteriores[2]}°C y {temp}°C: {cambio_frecuencia:.2f}"

        resultados_anteriores = (tiempo, frecuencia, temp)
