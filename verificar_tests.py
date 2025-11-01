"""
Script simple para verificar que los tests funcionan correctamente.
Ejecuta los 3 tests principales sin necesidad de pytest.
"""
import sys
import os

# Añadir el directorio raíz al path para importar los módulos
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from nucleo.base_conocimientos import KnowledgeBase


def test_1_inferencia_correcta():
    """Test 1: Inferencia correcta - humedad baja debe recomendar aumentar riego."""
    print("\n" + "="*70)
    print("TEST 1: INFERENCIA CORRECTA")
    print("="*70)
    
    try:
        kb = KnowledgeBase("data/plantas.json")
        
        planta = "Tomate"
        humedad_actual = 20  # Muy por debajo del óptimo (60-80)
        temperatura_actual = 25
        
        resultado = kb.recomendar_riego(planta, humedad_actual, temperatura_actual)
        
        print(f"\n📊 Condiciones:")
        print(f"   - Planta: {planta}")
        print(f"   - Humedad actual: {humedad_actual}%")
        print(f"   - Temperatura actual: {temperatura_actual}°C")
        print(f"\n📝 Resultado:")
        print(resultado)
        
        # Verificación
        if "aumentar riego" in resultado.lower():
            print("\n✅ TEST 1 PASADO: El sistema recomienda correctamente aumentar riego")
            return True
        else:
            print("\n❌ TEST 1 FALLIDO: No se detectó recomendación de aumentar riego")
            return False
            
    except Exception as e:
        print(f"\n❌ TEST 1 ERROR: {e}")
        return False


def test_2_caso_borde():
    """Test 2: Caso borde - validar comportamiento en límites del rango."""
    print("\n" + "="*70)
    print("TEST 2: CASO BORDE")
    print("="*70)
    
    try:
        kb = KnowledgeBase("data/plantas.json")
        
        planta = "Tomate"
        
        # Prueba en límite superior
        humedad_limite_sup = 80
        temperatura = 30
        
        resultado_sup = kb.recomendar_riego(planta, humedad_limite_sup, temperatura)
        
        print(f"\n📊 Condiciones (Límite Superior):")
        print(f"   - Planta: {planta}")
        print(f"   - Humedad actual: {humedad_limite_sup}% (límite superior)")
        print(f"   - Temperatura actual: {temperatura}°C")
        print(f"\n📝 Resultado:")
        print(resultado_sup)
        
        # Prueba en límite inferior
        humedad_limite_inf = 60
        resultado_inf = kb.recomendar_riego(planta, humedad_limite_inf, 25)
        
        print(f"\n📊 Condiciones (Límite Inferior):")
        print(f"   - Humedad actual: {humedad_limite_inf}% (límite inferior)")
        print(f"\n📝 Resultado:")
        print(resultado_inf)
        
        # Verificación
        check_sup = "humedad dentro del rango óptimo" in resultado_sup.lower() or \
                    "humedad alta" in resultado_sup.lower()
        check_inf = "humedad dentro del rango óptimo" in resultado_inf.lower() or \
                    "humedad baja" in resultado_inf.lower()
        
        if check_sup and check_inf:
            print("\n✅ TEST 2 PASADO: El sistema maneja correctamente los límites")
            return True
        else:
            print("\n❌ TEST 2 FALLIDO: No maneja correctamente los límites")
            return False
            
    except Exception as e:
        print(f"\n❌ TEST 2 ERROR: {e}")
        return False


def test_3_explicacion():
    """Test 3: Explicación - verificar mensajes claros de error y reglas."""
    print("\n" + "="*70)
    print("TEST 3: EXPLICACIÓN")
    print("="*70)
    
    try:
        kb = KnowledgeBase("data/plantas.json")
        
        # Parte A: Planta inexistente
        print("\n--- Parte A: Planta Inexistente ---")
        planta_inexistente = "PlantaFantasma123"
        resultado_error = kb.recomendar_riego(planta_inexistente, 50, 25)
        
        print(f"\n📊 Condiciones:")
        print(f"   - Planta: {planta_inexistente} (no existe)")
        print(f"\n📝 Resultado:")
        print(resultado_error)
        
        check_error = "no se encontró" in resultado_error.lower() or "❌" in resultado_error
        
        # Parte B: Reglas activadas
        print("\n--- Parte B: Reglas Activadas ---")
        planta = "Tomate"
        humedad = 40  # Baja
        temperatura = 32  # Alta
        
        resultado_reglas = kb.recomendar_riego(planta, humedad, temperatura)
        
        print(f"\n📊 Condiciones:")
        print(f"   - Planta: {planta}")
        print(f"   - Humedad actual: {humedad}% (baja)")
        print(f"   - Temperatura actual: {temperatura}°C (alta)")
        print(f"\n📝 Resultado:")
        print(resultado_reglas)
        
        check_reglas = "reglas activadas" in resultado_reglas.lower() or "📜" in resultado_reglas
        check_contenido = "humedad" in resultado_reglas.lower() and \
                          "temperatura" in resultado_reglas.lower()
        
        # Verificación final
        if check_error and check_reglas and check_contenido:
            print("\n✅ TEST 3 PASADO: El sistema genera explicaciones claras")
            return True
        else:
            print("\n❌ TEST 3 FALLIDO: Las explicaciones no son adecuadas")
            if not check_error:
                print("   - No detectó manejo de planta inexistente")
            if not check_reglas:
                print("   - No muestra reglas activadas")
            if not check_contenido:
                print("   - No explica las condiciones detectadas")
            return False
            
    except Exception as e:
        print(f"\n❌ TEST 3 ERROR: {e}")
        return False


def main():
    """Ejecuta todos los tests y muestra el resumen."""
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*15 + "SISTEMA EXPERTO DE RIEGO" + " "*29 + "║")
    print("║" + " "*20 + "TESTS AUTOMÁTICOS" + " "*31 + "║")
    print("╚" + "="*68 + "╝")
    
    resultados = []
    
    # Ejecutar los 3 tests principales
    resultados.append(("Test 1: Inferencia Correcta", test_1_inferencia_correcta()))
    resultados.append(("Test 2: Caso Borde", test_2_caso_borde()))
    resultados.append(("Test 3: Explicación", test_3_explicacion()))
    
    # Resumen final
    print("\n" + "="*70)
    print("RESUMEN DE TESTS")
    print("="*70)
    
    total = len(resultados)
    pasados = sum(1 for _, r in resultados if r)
    fallidos = total - pasados
    
    for nombre, resultado in resultados:
        estado = "✅ PASADO" if resultado else "❌ FALLIDO"
        print(f"{nombre}: {estado}")
    
    print("\n" + "-"*70)
    print(f"Total: {total} tests | ✅ Pasados: {pasados} | ❌ Fallidos: {fallidos}")
    print("-"*70)
    
    if pasados == total:
        print("\n🎉 ¡TODOS LOS TESTS PASARON EXITOSAMENTE! 🎉\n")
        return 0
    else:
        print(f"\n⚠️  {fallidos} test(s) fallaron. Revisa los detalles arriba.\n")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
