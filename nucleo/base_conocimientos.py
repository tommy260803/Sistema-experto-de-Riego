from __future__ import annotations
from typing import Dict, Any, List
import json
import os


class KnowledgeBase:
    """
    Clase encargada de manejar la base de conocimiento de plantas y reglas de riego.
    """

    def __init__(self, data_path="data/plantas.json"):
        self.data_path = os.path.abspath(data_path)
        self.plantas = self.cargar_datos()

    def cargar_datos(self):
        """Carga la información de las plantas desde el archivo JSON."""
        try:
            with open(self.data_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Convertimos la lista a diccionario con nombre original
                return {planta["nombre"]: planta for planta in data}
        except FileNotFoundError:
            print("⚠️ Archivo de plantas no encontrado, usando base vacía.")
            return {}

    def obtener_info_planta(self, nombre_planta):
        """Devuelve los parámetros de una planta específica."""
        return self.plantas.get(nombre_planta.title(), None)

    def recomendar_riego(self, nombre_planta, humedad_actual, temperatura_actual):
        """
        Devuelve una recomendación textual según las condiciones actuales comparadas
        con los valores óptimos y explica qué reglas se activaron.
        """
        planta = self.obtener_info_planta(nombre_planta)
        if not planta:
            return "❌ No se encontró información de esta planta."

        mensaje = f"🌿 Recomendación para {nombre_planta.capitalize()}:\n"
        reglas_activadas = []

        hum_min, hum_max = planta["humedad_suelo_opt"]
        temp_min, temp_max = planta["temperatura_opt"]

        # Evaluación de humedad
        if humedad_actual < hum_min:
            mensaje += "- Humedad baja: aumentar riego.\n"
            reglas_activadas.append("humedad_actual < humedad_optima → aumentar riego")
        elif humedad_actual > hum_max:
            mensaje += "- Humedad alta: reducir riego.\n"
            reglas_activadas.append("humedad_actual > humedad_optima → reducir riego")
        else:
            mensaje += "- Humedad dentro del rango óptimo.\n"
            reglas_activadas.append("humedad_actual dentro de rango → mantener riego")

        # Evaluación de temperatura
        if temperatura_actual < temp_min:
            mensaje += "- Temperatura baja: riego moderado.\n"
            reglas_activadas.append("temperatura_actual < temperatura_optima → riego moderado")
        elif temperatura_actual > temp_max:
            mensaje += "- Temperatura alta: aumentar riego.\n"
            reglas_activadas.append("temperatura_actual > temperatura_optima → aumentar riego")
        else:
            mensaje += "- Temperatura ideal para el cultivo.\n"
            reglas_activadas.append("temperatura_actual dentro de rango → riego normal")

        # Consejos adicionales de la planta
        mensaje += f"💡 Consejos: {planta['consejos']}\n"

        # Mostrar reglas activadas
        mensaje += "\n📜 Reglas activadas:\n"
        for regla in reglas_activadas:
            mensaje += f"- {regla}\n"

        return mensaje


kb = KnowledgeBase("data/plantas.json")
PLANT_KB: Dict[str, Dict[str, Any]] = kb.plantas
PLANTS = list(PLANT_KB.keys())


HISTORICO_PATH = os.path.join("data", "historico.json")


def _load_historico() -> List[Dict[str, Any]]:
    try:
        if os.path.exists(HISTORICO_PATH):
            with open(HISTORICO_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return []


def _save_historico(registros: List[Dict[str, Any]]) -> None:
    try:
        os.makedirs(os.path.dirname(HISTORICO_PATH), exist_ok=True)
        with open(HISTORICO_PATH, "w", encoding="utf-8") as f:
            json.dump(registros[-100:], f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def get_recomendacion(planta: str, condiciones: Dict[str, float], decision: Dict[str, float]) -> Dict[str, Any]:
    """Ajusta la recomendación según KB y guarda en historico.json (últimos 100).

    condiciones: {temperatura, humedad_suelo, prob_lluvia, humedad_ambiente, velocidad_viento}
    decision: {tiempo_min, frecuencia}
    """
    kb = PLANT_KB.get(planta, {})
    factor = float(kb.get("factor_ajuste", 1.0))
    tiempo_aj = float(decision.get("tiempo_min", 0)) * factor
    # Heurística simple: si humedad_suelo está por encima del óptimo, reducir 20%
    hs = float(condiciones.get("humedad_suelo", 0))
    opt = kb.get("humedad_suelo_opt", [0, 100])
    if hs > opt[1]:
        tiempo_aj *= 0.8
    if hs < opt[0]:
        tiempo_aj *= 1.1

    out = {
        "planta": planta,
        "tiempo_ajustado": max(0.0, min(60.0, tiempo_aj)),
        "frecuencia": float(decision.get("frecuencia", 0)),
        "consejos": kb.get("consejos", ""),
    }

    # Guardar en historico.json (mantener 100)
    registros = _load_historico()
    registros.append({
        **condiciones,
        "planta": planta,
        "tiempo_min": round(out["tiempo_ajustado"], 2),
        "frecuencia": round(out["frecuencia"], 2),
    })
    _save_historico(registros)
    return out
