import pytest
from nucleo.motor_difuso import FuzzyIrrigationSystem


def test_inferencia_correcta_suelo_seco():
    """Inferencia correcta - suelo seco debe activar reglas de riego intensivo."""
    sistema = FuzzyIrrigationSystem()

    # Condiciones de suelo seco extremo
    tiempo, frecuencia, activaciones = sistema.calculate_irrigation(
        temperature=35,      # Alta temperatura
        soil_humidity=10,    # Suelo muy seco
        rain_probability=5,  # Baja probabilidad de lluvia
        air_humidity=30,     # Aire seco
        wind_speed=10        # Viento moderado
    )

    # Verificar que se activan reglas críticas para suelo seco
    assert activaciones["R3"] > 0.8, f"R3 (suelo seco + lluvia baja) debería activarse fuertemente. Activación: {activaciones['R3']}"
    assert activaciones["R4"] > 0.8, f"R4 (temperatura alta + suelo seco) debería activarse. Activación: {activaciones['R4']}"

    # Verificar recomendaciones apropiadas
    assert tiempo >= 35, f"Tiempo de riego debería ser alto (>=35 min) para suelo seco. Tiempo: {tiempo}"
    assert frecuencia >= 2.5, f"Frecuencia debería ser alta (>=2.5 riegos/día). Frecuencia: {frecuencia}"

    # Verificar que reglas de humedad alta NO se activen
    assert activaciones["R8"] < 0.1, f"R8 (suelo húmedo) NO debería activarse. Activación: {activaciones['R8']}"


def test_inferencia_correcta_lluvia_alta():
    """Inferencia correcta - lluvia alta debe reducir significativamente el riego."""
    sistema = FuzzyIrrigationSystem()

    # Condiciones de lluvia abundante
    tiempo_lluvia, frecuencia_lluvia, activaciones = sistema.calculate_irrigation(
        temperature=22,      # Temperatura moderada
        soil_humidity=60,    # Humedad moderada
        rain_probability=85, # Alta probabilidad de lluvia
        air_humidity=80,     # Aire húmedo
        wind_speed=8         # Viento bajo
    )

    # Comparar con condiciones sin lluvia
    tiempo_normal, frecuencia_normal, _ = sistema.calculate_irrigation(
        temperature=22,      # Temperatura moderada
        soil_humidity=60,    # Humedad moderada
        rain_probability=10, # Baja probabilidad de lluvia
        air_humidity=80,     # Aire húmedo
        wind_speed=8         # Viento bajo
    )

    # Verificar que se activa la regla crítica de lluvia alta
    assert activaciones["R1"] > 0.9, f"R1 (lluvia alta) debería activarse completamente. Activación: {activaciones['R1']}"

    # Verificar que el riego se reduce con lluvia (al menos 20% menos)
    assert tiempo_lluvia < tiempo_normal * 0.9, f"Tiempo con lluvia ({tiempo_lluvia:.1f}) debería ser menor que sin lluvia ({tiempo_normal:.1f})"
    assert frecuencia_lluvia <= frecuencia_normal, f"Frecuencia con lluvia ({frecuencia_lluvia:.1f}) debería ser igual o menor que sin lluvia ({frecuencia_normal:.1f})"

    # Verificar que sigue siendo un valor razonable
    assert tiempo_lluvia <= 15, f"Tiempo de riego con lluvia alta debería ser moderado. Tiempo: {tiempo_lluvia}"
    assert frecuencia_lluvia <= 2.0, f"Frecuencia con lluvia alta debería ser baja-moderada. Frecuencia: {frecuencia_lluvia}"


def test_inferencia_correcta_condiciones_balanceadas():
    """Inferencia correcta - condiciones moderadas deben dar recomendaciones equilibradas."""
    sistema = FuzzyIrrigationSystem()

    # Condiciones moderadas/balanceadas
    tiempo, frecuencia, activaciones = sistema.calculate_irrigation(
        temperature=25,      # Temperatura media
        soil_humidity=60,    # Humedad moderada
        rain_probability=30, # Lluvia media
        air_humidity=50,     # Humedad media
        wind_speed=10        # Viento bajo
    )

    # Verificar que se activa la regla de condiciones balanceadas
    assert activaciones["R23"] > 0.6, f"R23 (condiciones balanceadas) debería activarse. Activación: {activaciones['R23']}"

    # Verificar recomendaciones moderadas
    assert 15 <= tiempo <= 35, f"Tiempo debería ser moderado (15-35 min). Tiempo: {tiempo}"
    assert 1.5 <= frecuencia <= 2.5, f"Frecuencia debería ser media (1.5-2.5 riegos/día). Frecuencia: {frecuencia}"
