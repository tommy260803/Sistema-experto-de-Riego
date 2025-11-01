"""
Tests del Sistema Experto de Riego
Pruebas automáticas para validar inferencia, casos borde y explicaciones.
"""
import pytest
from nucleo.base_conocimientos import KnowledgeBase, PLANT_KB
from nucleo.motor_difuso import FuzzyIrrigationSystem


class TestInferenciaCorrecta:
    """Test 1: Verifica que la inferencia básica funcione correctamente."""
    
    def test_recomendacion_humedad_baja(self):
        """
        Prueba de inferencia correcta:
        Si la humedad del suelo es baja (< rango óptimo), 
        el sistema debe recomendar "aumentar riego".
        """
        kb = KnowledgeBase("data/plantas.json")
        
        # Condiciones: humedad muy baja (20%) para Tomate
        # Rango óptimo de Tomate: humedad_suelo_opt = [60, 80]
        planta = "Tomate"
        humedad_actual = 20  # Muy por debajo del óptimo (60-80)
        temperatura_actual = 25  # Dentro del rango óptimo
        
        resultado = kb.recomendar_riego(planta, humedad_actual, temperatura_actual)
        
        # Verificaciones
        assert "aumentar riego" in resultado.lower(), \
            "El sistema debería recomendar aumentar riego con humedad baja"
        assert "humedad_actual < humedad_optima" in resultado.lower() or \
               "humedad baja" in resultado.lower(), \
            "La explicación debe mencionar humedad baja o la regla activada"
        
        print("\n✅ Test 1 - Inferencia correcta: PASADO")
        print(f"Resultado: {resultado}")


class TestCasoBorde:
    """Test 2: Valida el comportamiento en los límites de los rangos."""
    
    def test_recomendacion_en_limite_rango(self):
        """
        Prueba de caso borde:
        Si la humedad está justo en el límite superior del rango óptimo,
        el sistema debe mantener o reducir ligeramente el riego.
        """
        kb = KnowledgeBase("data/plantas.json")
        
        # Condiciones: humedad en el límite superior para Tomate
        # Rango óptimo de Tomate: humedad_suelo_opt = [60, 80]
        planta = "Tomate"
        humedad_limite = 80  # Justo en el límite superior
        temperatura_limite = 30  # Justo en el límite superior de temp (18-30)
        
        resultado = kb.recomendar_riego(planta, humedad_limite, temperatura_limite)
        
        # Verificaciones: debe estar en rango o apenas salirse
        assert "humedad dentro del rango óptimo" in resultado.lower() or \
               "humedad alta" in resultado.lower(), \
            "El sistema debe reconocer que está en el límite o ligeramente fuera"
        
        # Test adicional: justo en el límite inferior
        humedad_limite_inf = 60
        resultado_inf = kb.recomendar_riego(planta, humedad_limite_inf, 25)
        
        assert "humedad dentro del rango óptimo" in resultado_inf.lower() or \
               "humedad baja" in resultado_inf.lower(), \
            "El sistema debe manejar correctamente el límite inferior"
        
        print("\n✅ Test 2 - Caso borde: PASADO")
        print(f"Resultado límite superior: {resultado}")
        print(f"Resultado límite inferior: {resultado_inf}")


class TestExplicacion:
    """Test 3: Verifica que el sistema genera explicaciones claras."""
    
    def test_explicacion_planta_no_existente(self):
        """
        Prueba de explicación:
        Si se consulta una planta que no existe en la base de conocimiento,
        el sistema debe explicar claramente por qué no puede dar una recomendación.
        """
        kb = KnowledgeBase("data/plantas.json")
        
        planta_inexistente = "PlantaFantasma123"
        humedad = 50
        temperatura = 25
        
        resultado = kb.recomendar_riego(planta_inexistente, humedad, temperatura)
        
        # Verificaciones
        assert "no se encontró" in resultado.lower() or \
               "❌" in resultado, \
            "El sistema debe indicar claramente que la planta no existe"
        
        print("\n✅ Test 3 - Explicación (planta no existente): PASADO")
        print(f"Resultado: {resultado}")
    
    def test_explicacion_reglas_activadas(self):
        """
        Prueba adicional de explicación:
        El sistema debe listar las reglas que se activaron para tomar la decisión.
        """
        kb = KnowledgeBase("data/plantas.json")
        
        # Condiciones que activarán múltiples reglas
        planta = "Tomate"
        humedad = 40  # Baja (< 60)
        temperatura = 32  # Alta (> 30)
        
        resultado = kb.recomendar_riego(planta, humedad, temperatura)
        
        # Verificaciones
        assert "reglas activadas" in resultado.lower() or \
               "📜" in resultado, \
            "El sistema debe mostrar las reglas activadas"
        
        # Debe mencionar ambas condiciones problemáticas
        assert ("humedad" in resultado.lower() and "aumentar" in resultado.lower()) or \
               "humedad_actual < humedad_optima" in resultado.lower(), \
            "Debe explicar la decisión sobre humedad"
        
        assert ("temperatura" in resultado.lower() and "aumentar" in resultado.lower()) or \
               "temperatura_actual > temperatura_optima" in resultado.lower(), \
            "Debe explicar la decisión sobre temperatura"
        
        print("\n✅ Test 3b - Explicación (reglas activadas): PASADO")
        print(f"Resultado: {resultado}")


class TestMotorDifuso:
    """Tests adicionales para el motor difuso (bonus)."""
    
    def test_motor_difuso_basico(self):
        """
        Verifica que el motor difuso calcula valores coherentes.
        """
        motor = FuzzyIrrigationSystem()
        
        # Condiciones extremas: mucho calor, suelo seco, sin lluvia
        resultado = motor.calcular_riego(
            temperature=35,
            soil_humidity=20,
            rain_probability=5,
            air_humidity=30,
            wind_speed=15
        )
        
        # Verificaciones
        assert resultado.tiempo_min > 0, "El tiempo de riego debe ser positivo"
        assert resultado.frecuencia > 0, "La frecuencia debe ser positiva"
        assert 0 <= resultado.confianza <= 1, "La confianza debe estar entre 0 y 1"
        assert len(resultado.explicacion) > 0, "Debe generar una explicación"
        
        print("\n✅ Test Bonus - Motor difuso básico: PASADO")
        print(f"Tiempo: {resultado.tiempo_min:.2f} min")
        print(f"Frecuencia: {resultado.frecuencia:.2f} veces/día")
        print(f"Confianza: {resultado.confianza:.2%}")


if __name__ == "__main__":
    """Permite ejecutar los tests directamente desde este archivo."""
    print("=" * 60)
    print("EJECUTANDO TESTS DEL SISTEMA EXPERTO DE RIEGO")
    print("=" * 60)
    
    # Test 1: Inferencia correcta
    test1 = TestInferenciaCorrecta()
    test1.test_recomendacion_humedad_baja()
    
    # Test 2: Caso borde
    test2 = TestCasoBorde()
    test2.test_recomendacion_en_limite_rango()
    
    # Test 3: Explicación
    test3 = TestExplicacion()
    test3.test_explicacion_planta_no_existente()
    test3.test_explicacion_reglas_activadas()
    
    # Test Bonus: Motor difuso
    test4 = TestMotorDifuso()
    test4.test_motor_difuso_basico()
    
    print("\n" + "=" * 60)
    print("TODOS LOS TESTS COMPLETADOS ✅")
    print("=" * 60)
