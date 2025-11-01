import pytest
from nucleo.motor_difuso import FuzzyIrrigationSystem
from nucleo.base_conocimientos import get_recomendacion, PLANT_KB
from nucleo.utilidades import validate_inputs


def test_integracion_completa_sistema():
    """TEST MÁS IMPORTANTE: Validación end-to-end completa del sistema de riego inteligente

    Este test verifica el flujo completo desde datos de sensores hasta recomendaciones finales,
    simulando el uso real del sistema por un agricultor.
    """
    # 🏗️ FASE 1: Simulación de datos de sensores reales
    sensor_data = {
        'temperature': 28.5,      # Temperatura moderada-alta
        'soil_humidity': 35.2,    # Suelo seco (requiere riego)
        'rain_probability': 15.8, # Baja probabilidad de lluvia
        'air_humidity': 52.1,     # Humedad media
        'wind_speed': 12.3        # Viento moderado
    }

    planta_seleccionada = "Tomate"

    # ✅ Verificar que los datos de entrada son válidos
    validate_inputs(
        sensor_data['temperature'],
        sensor_data['soil_humidity'],
        sensor_data['rain_probability'],
        sensor_data['air_humidity'],
        sensor_data['wind_speed']
    )

    # 🧠 FASE 2: Motor difuso procesa las condiciones ambientales
    sistema = FuzzyIrrigationSystem()
    tiempo_calculado, frecuencia_calculada, activaciones = sistema.calculate_irrigation(**sensor_data)

    # ✅ Verificar que el motor difuso produce resultados válidos
    assert 0 <= tiempo_calculado <= 60, f"Tiempo de riego fuera de rango: {tiempo_calculado}"
    assert 0.5 <= frecuencia_calculada <= 4, f"Frecuencia fuera de rango: {frecuencia_calculada}"
    assert isinstance(activaciones, dict), "Activaciones no es un diccionario"
    assert len(activaciones) > 0, "No hay activaciones de reglas"

    # 📚 FASE 3: Base de conocimientos ajusta según la planta específica
    decision_motor = {"tiempo_min": tiempo_calculado, "frecuencia": frecuencia_calculada}
    recomendacion_final = get_recomendacion(planta_seleccionada, sensor_data, decision_motor)

    # ✅ Verificar que la recomendación es completa y coherente
    assert isinstance(recomendacion_final, dict), "Recomendación no es un diccionario"
    assert 'tiempo_ajustado' in recomendacion_final, "Falta tiempo ajustado en recomendación"
    assert 'frecuencia' in recomendacion_final, "Falta frecuencia en recomendación"
    assert 'consejos' in recomendacion_final, "Faltan consejos en recomendación"

    # ✅ Verificar rangos finales
    assert 0 <= recomendacion_final['tiempo_ajustado'] <= 60, \
        f"Tiempo ajustado fuera de rango: {recomendacion_final['tiempo_ajustado']}"
    assert 0.5 <= recomendacion_final['frecuencia'] <= 4, \
        f"Frecuencia final fuera de rango: {recomendacion_final['frecuencia']}"

    # 🎯 FASE 4: Verificar lógica de negocio específica
    # En condiciones de suelo seco (35%), debería recomendar riego
    assert recomendacion_final['tiempo_ajustado'] > 10, \
        f"Con suelo seco (35%) debería recomendar más riego. Tiempo: {recomendacion_final['tiempo_ajustado']}"

    # Verificar que incluye consejos específicos del tomate
    consejos = recomendacion_final['consejos'].lower()
    assert 'encharcamiento' in consejos or 'humedad' in consejos, \
        f"Los consejos no mencionan precauciones del tomate: {recomendacion_final['consejos']}"

    # 📊 FASE 5: Verificar explicabilidad del sistema
    explicacion = sistema.explain_decision(tiempo_calculado, frecuencia_calculada, activaciones)
    assert isinstance(explicacion, str), "Explicación no es texto"
    assert len(explicacion) > 20, "Explicación demasiado corta"
    assert "reglas" in explicacion.lower(), "Explicación no menciona reglas activadas"


def test_integracion_completa_multiples_plantas():
    """Validar integración completa con diferentes tipos de plantas"""
    sistema = FuzzyIrrigationSystem()

    condiciones_base = {
        'temperature': 25.0,
        'soil_humidity': 50.0,
        'rain_probability': 20.0,
        'air_humidity': 60.0,
        'wind_speed': 10.0
    }

    plantas_prueba = ['Tomate', 'Lechuga', 'Zanahoria']

    for planta in plantas_prueba:
        # Calcular riego
        tiempo, frecuencia, _ = sistema.calculate_irrigation(**condiciones_base)

        # Obtener recomendación específica
        recomendacion = get_recomendacion(planta, condiciones_base, {"tiempo_min": tiempo, "frecuencia": frecuencia})

        # Verificar integridad
        assert isinstance(recomendacion, dict), f"Recomendación de {planta} no es diccionario"
        assert 'tiempo_ajustado' in recomendacion, f"Falta tiempo en recomendación de {planta}"
        assert 'consejos' in recomendacion, f"Faltan consejos para {planta}"

        # Verificar que el factor de ajuste de planta se aplicó correctamente
        # (no verificamos valor exacto debido a lógica adicional de humedad)
        factor_planta = PLANT_KB[planta]['factor_ajuste']
        tiempo_base_ajustado = tiempo * factor_planta

        # Verificar que el tiempo ajustado es razonable (no negativo, no > 60)
        assert 0 <= recomendacion['tiempo_ajustado'] <= 60, \
            f"Tiempo ajustado de {planta} fuera de rango: {recomendacion['tiempo_ajustado']}"

        # Verificar que el ajuste se aplicó (permitiendo lógica adicional de humedad)
        # El tiempo ajustado debería estar cerca del tiempo base ajustado
        diferencia_aceptable = max(5.0, tiempo_base_ajustado * 0.3)  # 30% de tolerancia
        assert abs(recomendacion['tiempo_ajustado'] - tiempo_base_ajustado) <= diferencia_aceptable, \
            f"Ajuste de planta {planta} demasiado diferente. Base: {tiempo_base_ajustado}, Obtenido: {recomendacion['tiempo_ajustado']}"


def test_integracion_completa_casos_criticos():
    """Validar integración en escenarios críticos que requieren acción inmediata"""
    sistema = FuzzyIrrigationSystem()

    # Escenario crítico: suelo muy seco
    condiciones_criticas = {
        'temperature': 35.0,     # Muy alta
        'soil_humidity': 15.0,   # Muy seca
        'rain_probability': 5.0, # Sin lluvia
        'air_humidity': 25.0,    # Muy seca
        'wind_speed': 20.0       # Viento alto
    }

    tiempo, frecuencia, activaciones = sistema.calculate_irrigation(**condiciones_criticas)
    recomendacion = get_recomendacion("Tomate", condiciones_criticas, {"tiempo_min": tiempo, "frecuencia": frecuencia})

    # En condiciones críticas, debería recomendar riego intensivo
    assert recomendacion['tiempo_ajustado'] >= 30, \
        f"En condiciones críticas debería recomendar riego intensivo. Tiempo: {recomendacion['tiempo_ajustado']}"

    assert recomendacion['frecuencia'] >= 2.0, \
        f"En condiciones críticas debería recomendar frecuencia alta. Frecuencia: {recomendacion['frecuencia']}"

    # Verificar que se activan reglas críticas
    reglas_criticas_activadas = sum(1 for regla, activacion in activaciones.items()
                                   if activacion > 0.7 and regla in ['R3', 'R4', 'R7'])
    assert reglas_criticas_activadas >= 2, \
        f"Deberían activarse al menos 2 reglas críticas. Reglas críticas: {reglas_criticas_activadas}"
