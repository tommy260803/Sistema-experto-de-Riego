import pytest
from nucleo.base_conocimientos import KnowledgeBase

# ---------- TEST 1 ----------
def test_inferencia_correcta():
    """Inferencia correcta - humedad baja debe recomendar aumentar riego."""
    kb = KnowledgeBase("data/plantas.json")

    planta = "Tomate"
    humedad_actual = 20
    temperatura_actual = 25

    resultado = kb.recomendar_riego(planta, humedad_actual, temperatura_actual).lower()

    assert "aumentar riego" in resultado, \
        f"No se detectó recomendación de aumentar riego. Resultado: {resultado}"


# ---------- TEST 2 ----------
def test_caso_borde():
    """Caso borde - validar comportamiento en los límites del rango."""
    kb = KnowledgeBase("data/plantas.json")
    planta = "Tomate"

    humedad_limite_sup = 80
    humedad_limite_inf = 60

    resultado_sup = kb.recomendar_riego(planta, humedad_limite_sup, 30).lower()
    resultado_inf = kb.recomendar_riego(planta, humedad_limite_inf, 25).lower()

    check_sup = ("humedad dentro del rango óptimo" in resultado_sup) or ("humedad alta" in resultado_sup)
    check_inf = ("humedad dentro del rango óptimo" in resultado_inf) or ("humedad baja" in resultado_inf)

    assert check_sup and check_inf, \
        f"No maneja correctamente los límites. Sup: {resultado_sup} | Inf: {resultado_inf}"


# ---------- TEST 3 ----------
def test_explicacion():
    """Explicación - mensajes claros ante errores y reglas activadas."""
    kb = KnowledgeBase("data/plantas.json")

    # Parte A: planta inexistente
    resultado_error = kb.recomendar_riego("PlantaFantasma123", 50, 25)
    check_error = ("no se encontró" in resultado_error.lower()) or ("❌" in resultado_error)

    # Parte B: reglas activadas
    resultado_reglas = kb.recomendar_riego("Tomate", 40, 32)
    resultado_reglas_l = resultado_reglas.lower()

    check_reglas = ("reglas activadas" in resultado_reglas_l) or ("📜" in resultado_reglas_l)
    check_contenido = "humedad" in resultado_reglas_l and "temperatura" in resultado_reglas_l

    assert check_error, "No se detectó manejo de planta inexistente."
    assert check_reglas, "No muestra reglas activadas."
    assert check_contenido, "No explica las condiciones detectadas."
