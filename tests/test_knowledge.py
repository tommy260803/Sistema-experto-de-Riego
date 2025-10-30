# tests/test_knowledge.py
import pytest
from nucleo.base_conocimientos import KnowledgeBase

@pytest.fixture
def kb():
    return KnowledgeBase()

def test_recomendacion_basica(kb):
    mensaje = kb.recomendar_riego("tomate", humedad_actual=40, temperatura_actual=28)
    assert "aumentar riego" in mensaje.lower()

def test_recomendacion_borde(kb):
    # Humedad al límite inferior
    mensaje = kb.recomendar_riego("lechuga", humedad_actual=60, temperatura_actual=24)
    assert "dentro del rango óptimo" in mensaje.lower() or "ideal" in mensaje.lower()

def test_planta_no_existente(kb):
    mensaje = kb.recomendar_riego("planta_fantasma", humedad_actual=50, temperatura_actual=20)
    assert "no se encontró información" in mensaje.lower()
