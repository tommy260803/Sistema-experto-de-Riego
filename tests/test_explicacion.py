import pytest
from nucleo.motor_difuso import FuzzyIrrigationSystem
from nucleo.base_conocimientos import KnowledgeBase, get_recomendacion


def test_explicacion_reglas_activadas():
    """Explicación - el sistema debe mostrar qué reglas se activaron y por qué."""
    sistema = FuzzyIrrigationSystem()

    # Condición específica que active reglas conocidas
    tiempo, frecuencia, activaciones = sistema.calculate_irrigation(
        temperature=35,      # Alta temperatura
        soil_humidity=15,    # Suelo seco
        rain_probability=10, # Baja lluvia
        air_humidity=25,     # Aire seco
        wind_speed=15        # Viento moderado
    )

    # Generar explicación
    explicacion = sistema.explain_decision(tiempo, frecuencia, activaciones)

    # Verificar que la explicación incluye información clave
    explicacion_lower = explicacion.lower()

    # Debe mencionar tiempo y frecuencia
    assert "tiempo" in explicacion_lower, "Explicación no menciona el tiempo de riego"
    assert "frecuencia" in explicacion_lower, "Explicación no menciona la frecuencia"

    # Debe mostrar las reglas más activas
    assert "reglas más activas" in explicacion_lower or "top" in explicacion_lower, \
        "Explicación no muestra reglas activadas"

    # Verificar que las reglas críticas aparecen en la explicación
    # R3 (suelo seco + lluvia baja) debería estar activada
    assert "R3" in explicacion or "R4" in explicacion, \
        "Explicación no muestra reglas críticas activadas"

    # Verificar formato de explicación
    assert "⏱️" in explicacion, "Explicación no tiene formato con emojis"
    assert "🔄" in explicacion, "Explicación no muestra frecuencia"


def test_explicacion_recomendaciones_planta():
    """Explicación - sistema debe explicar recomendaciones específicas por planta."""
    kb = KnowledgeBase("data/plantas.json")

    # Probar con tomate en condiciones de estrés
    planta = "Tomate"
    humedad_actual = 25  # Baja humedad
    temperatura_actual = 32  # Alta temperatura

    resultado = kb.recomendar_riego(planta, humedad_actual, temperatura_actual)
    resultado_lower = resultado.lower()

    # Verificar que explica las condiciones detectadas
    assert "humedad baja" in resultado_lower or "aumentar riego" in resultado_lower, \
        "No explica condición de humedad baja"

    assert "temperatura alta" in resultado_lower or "aumentar riego" in resultado_lower, \
        "No explica condición de temperatura alta"

    # Verificar que muestra reglas activadas
    assert "reglas activadas" in resultado_lower, \
        "No muestra sección de reglas activadas"

    # Verificar consejos específicos del tomate
    assert "encharcamientos" in resultado_lower, \
        "No incluye consejos específicos del tomate"


def test_explicacion_manejo_errores():
    """Explicación - sistema debe explicar errores y casos no encontrados."""
    kb = KnowledgeBase("data/plantas.json")

    # Planta inexistente
    resultado_error = kb.recomendar_riego("PlantaFantasma123", 50, 25)

    assert "no se encontró" in resultado_error.lower() or "❌" in resultado_error, \
        "No maneja correctamente plantas inexistentes"

    # Verificar que da una respuesta coherente aunque sea de error
    assert len(resultado_error) > 10, "Mensaje de error demasiado corto"


def test_explicacion_decisiones_balanceadas():
    """Explicación - sistema debe explicar decisiones en condiciones normales."""
    sistema = FuzzyIrrigationSystem()

    # Condiciones moderadas
    tiempo, frecuencia, activaciones = sistema.calculate_irrigation(
        temperature=25,      # Moderada
        soil_humidity=55,    # Moderada
        rain_probability=25, # Moderada
        air_humidity=55,     # Moderada
        wind_speed=12        # Moderada
    )

    explicacion = sistema.explain_decision(tiempo, frecuencia, activaciones)

    # Debe mostrar reglas activadas (lo cual indica funcionamiento normal)
    explicacion_lower = explicacion.lower()
    assert "reglas" in explicacion_lower, \
        "No muestra reglas activadas en condiciones normales"
    assert "r10" in explicacion_lower or "r17" in explicacion_lower or "r19" in explicacion_lower, \
        f"No muestra reglas esperadas. Explicación: {explicacion}"

    # No debería mostrar alertas de condiciones extremas
    assert "urgente" not in explicacion_lower and "extremas" not in explicacion_lower, \
        "Incorrectamente muestra alertas en condiciones normales"


def test_explicacion_flujo_completo():
    """Explicación - validar flujo completo desde inputs hasta recomendaciones."""
    from nucleo.base_conocimientos import get_recomendacion

    # Simular flujo completo
    inputs = {
        "temperatura": 28,
        "humedad_suelo": 35,
        "prob_lluvia": 15,
        "humedad_ambiente": 45,
        "velocidad_viento": 18
    }

    # Calcular riego
    sistema = FuzzyIrrigationSystem()
    tiempo, frecuencia, activaciones = sistema.calculate_irrigation(
        temperature=inputs["temperatura"],
        soil_humidity=inputs["humedad_suelo"],
        rain_probability=inputs["prob_lluvia"],
        air_humidity=inputs["humedad_ambiente"],
        wind_speed=inputs["velocidad_viento"]
    )

    # Generar explicación del motor
    explicacion_motor = sistema.explain_decision(tiempo, frecuencia, activaciones)

    # Obtener recomendaciones de planta
    recomendacion_planta = get_recomendacion("Tomate", inputs, {"tiempo_min": tiempo, "frecuencia": frecuencia})

    # Verificar que ambas explicaciones son coherentes
    assert isinstance(explicacion_motor, str) and len(explicacion_motor) > 50, \
        "Explicación del motor difuso es insuficiente"

    assert isinstance(recomendacion_planta, dict), \
        "Recomendación de planta no tiene formato correcto"

    assert "tiempo_ajustado" in recomendacion_planta, \
        "Recomendación no incluye tiempo ajustado"

    assert "frecuencia" in recomendacion_planta, \
        "Recomendación no incluye frecuencia"

    assert "consejos" in recomendacion_planta, \
        "Recomendación no incluye consejos específicos"


def test_explicacion_sensibilidad():
    """Explicación - sistema debe manejar análisis de sensibilidad correctamente."""
    from nucleo.visualizadores.sensibilidad import VisualizadorSensibilidad
    from nucleo.visualizadores.configuracion import VisualizationConfig

    sistema = FuzzyIrrigationSystem()
    config = VisualizationConfig()
    visualizador = VisualizadorSensibilidad(sistema, config)

    # Condición base para análisis
    base_scenario = {
        'temperature': 25.0,
        'soil_humidity': 50.0,
        'rain_probability': 20.0,
        'air_humidity': 60.0,
        'wind_speed': 10.0
    }

    # Verificar que el visualizador se puede crear sin errores
    assert visualizador is not None, "No se puede crear el visualizador de sensibilidad"

    # Verificar que puede calcular activaciones sin errores
    try:
        tiempo, frecuencia, activaciones = sistema.calculate_irrigation(**base_scenario)
        assert isinstance(activaciones, dict), "Las activaciones no son un diccionario"
        assert len(activaciones) > 0, "No hay activaciones calculadas"
        assert all(isinstance(v, (int, float)) for v in activaciones.values()), "Las activaciones no son numéricas"
    except Exception as e:
        pytest.fail(f"Error al calcular activaciones: {e}")

    # Verificar que el sistema puede manejar diferentes escenarios sin errores
    escenarios = [
        {'temperature': 15.0, **{k: v for k, v in base_scenario.items() if k != 'temperature'}},
        {'temperature': 35.0, **{k: v for k, v in base_scenario.items() if k != 'temperature'}},
        {'soil_humidity': 20.0, **{k: v for k, v in base_scenario.items() if k != 'soil_humidity'}},
        {'soil_humidity': 80.0, **{k: v for k, v in base_scenario.items() if k != 'soil_humidity'}},
    ]

    for escenario in escenarios:
        try:
            t, f, act = sistema.calculate_irrigation(**escenario)
            assert 0 <= t <= 60, f"Tiempo fuera de rango en escenario: {escenario}"
            assert 0.5 <= f <= 4, f"Frecuencia fuera de rango en escenario: {escenario}"
        except Exception as e:
            pytest.fail(f"Error en escenario {escenario}: {e}")
