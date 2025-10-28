from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Tuple, Any, List
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl

# Universos de discurso
TEMP_UNIVERSE = np.linspace(0, 50, 501)
SOIL_UNIVERSE = np.linspace(0, 100, 501)
RAIN_UNIVERSE = np.linspace(0, 100, 501)
AIRH_UNIVERSE = np.linspace(0, 100, 501)
WIND_UNIVERSE = np.linspace(0, 50, 501)
TIME_UNIVERSE = np.linspace(0, 60, 601)
FREQ_UNIVERSE = np.linspace(0, 4, 401)


@dataclass
class ResultadoDifuso:
    tiempo_min: float
    frecuencia: float
    activaciones: Dict[str, float]
    explicacion: str


class SistemaRiegoDifuso:
    """Sistema de Riego Inteligente basado en Lógica Difusa (Mamdani)."""

    def __init__(self) -> None:
        self._build_system()

    def _build_system(self) -> None:
        # Definir variables
        self.temperatura = ctrl.Antecedent(TEMP_UNIVERSE, "temperatura")
        self.h_suelo = ctrl.Antecedent(SOIL_UNIVERSE, "humedad_suelo")
        self.lluvia = ctrl.Antecedent(RAIN_UNIVERSE, "lluvia")
        self.h_aire = ctrl.Antecedent(AIRH_UNIVERSE, "humedad_aire")
        self.viento = ctrl.Antecedent(WIND_UNIVERSE, "viento")
        self.tiempo = ctrl.Consequent(TIME_UNIVERSE, "tiempo")
        self.frecuencia = ctrl.Consequent(FREQ_UNIVERSE, "frecuencia")

        # Funciones de membresía (triangulares/trapezoidales) segun especificación
        self.temperatura["baja"] = fuzz.trapmf(TEMP_UNIVERSE, [0, 0, 10, 20])
        self.temperatura["media"] = fuzz.trimf(TEMP_UNIVERSE, [15, 25, 30])
        self.temperatura["alta"] = fuzz.trapmf(TEMP_UNIVERSE, [25, 30, 50, 50])

        self.h_suelo["seca"] = fuzz.trapmf(SOIL_UNIVERSE, [0, 0, 15, 30])
        self.h_suelo["moderada"] = fuzz.trapmf(SOIL_UNIVERSE, [20, 35, 45, 60])
        self.h_suelo["humeda"] = fuzz.trapmf(SOIL_UNIVERSE, [50, 70, 100, 100])

        self.lluvia["baja"] = fuzz.trapmf(RAIN_UNIVERSE, [0, 0, 15, 30])
        self.lluvia["media"] = fuzz.trapmf(RAIN_UNIVERSE, [20, 35, 45, 60])
        self.lluvia["alta"] = fuzz.trapmf(RAIN_UNIVERSE, [50, 70, 100, 100])

        self.h_aire["baja"] = fuzz.trapmf(AIRH_UNIVERSE, [0, 0, 20, 40])
        self.h_aire["media"] = fuzz.trapmf(AIRH_UNIVERSE, [30, 45, 55, 70])
        self.h_aire["alta"] = fuzz.trapmf(AIRH_UNIVERSE, [60, 80, 100, 100])

        self.viento["bajo"] = fuzz.trapmf(WIND_UNIVERSE, [0, 0, 8, 15])
        self.viento["medio"] = fuzz.trapmf(WIND_UNIVERSE, [10, 18, 25, 30])
        self.viento["alto"] = fuzz.trapmf(WIND_UNIVERSE, [25, 35, 50, 50])

        self.tiempo["nulo"] = fuzz.trapmf(TIME_UNIVERSE, [0, 0, 3, 5])
        self.tiempo["corto"] = fuzz.trapmf(TIME_UNIVERSE, [3, 8, 15, 20])
        self.tiempo["medio"] = fuzz.trapmf(TIME_UNIVERSE, [15, 22, 33, 40])
        self.tiempo["largo"] = fuzz.trapmf(TIME_UNIVERSE, [35, 45, 60, 60])

        self.frecuencia["baja"] = fuzz.trapmf(FREQ_UNIVERSE, [0.5, 0.75, 1.25, 1.5])
        self.frecuencia["media"] = fuzz.trapmf(FREQ_UNIVERSE, [1.0, 1.5, 2.0, 2.5])
        self.frecuencia["alta"] = fuzz.trapmf(FREQ_UNIVERSE, [2.0, 2.5, 3.5, 4.0])

        # Reglas (30+)
        rules: List[ctrl.Rule] = []
        R = ctrl.Rule
        # 1
        rules.append(R(self.h_suelo["seca"] & self.lluvia["baja"], (self.tiempo["largo"], self.frecuencia["alta"])) )
        # 2
        rules.append(R(self.h_suelo["humeda"], (self.tiempo["corto"], self.frecuencia["baja"])) )
        # 3
        rules.append(R(self.temperatura["alta"] & self.h_suelo["seca"], self.tiempo["largo"]))
        # 4
        rules.append(R(self.lluvia["alta"], self.tiempo["nulo"]))
        # 5
        rules.append(R(self.viento["alto"] & self.temperatura["alta"], self.frecuencia["alta"]))
        # 6
        rules.append(R(self.temperatura["baja"] & self.h_aire["alta"], self.tiempo["corto"]))
        # 7
        rules.append(R(self.h_suelo["moderada"] & self.lluvia["media"], self.tiempo["corto"]))
        # 8
        rules.append(R(self.temperatura["alta"] & self.h_aire["baja"] & self.viento["bajo"], self.tiempo["largo"]))
        # 9
        rules.append(R(self.viento["alto"] & self.lluvia["baja"], self.frecuencia["alta"]))
        # 10
        rules.append(R(self.h_aire["baja"] & self.h_suelo["seca"], (self.tiempo["largo"], self.frecuencia["alta"])) )
        # 11
        rules.append(R(self.h_aire["alta"] & self.lluvia["media"], self.tiempo["corto"]))
        # 12
        rules.append(R(self.temperatura["media"] & self.h_suelo["moderada"], self.tiempo["medio"]))
        # 13
        rules.append(R(self.temperatura["media"] & self.lluvia["baja"], self.frecuencia["media"]))
        # 14
        rules.append(R(self.temperatura["alta"] & self.viento["medio"], self.frecuencia["alta"]))
        # 15
        rules.append(R(self.h_suelo["seca"] & self.viento["alto"], self.tiempo["largo"]))
        # 16
        rules.append(R(self.h_suelo["moderada"] & self.viento["bajo"], self.frecuencia["media"]))
        # 17
        rules.append(R(self.h_aire["media"] & self.lluvia["baja"], self.tiempo["medio"]))
        # 18
        rules.append(R(self.temperatura["baja"] & self.lluvia["alta"], self.tiempo["nulo"]))
        # 19
        rules.append(R(self.h_aire["baja"] & self.viento["alto"], self.frecuencia["alta"]))
        # 20
        rules.append(R(self.h_suelo["humeda"] & self.lluvia["alta"], (self.tiempo["nulo"], self.frecuencia["baja"])) )
        # 21
        rules.append(R(self.temperatura["alta"] & self.lluvia["media"] & self.viento["alto"], self.tiempo["medio"]))
        # 22
        rules.append(R(self.temperatura["media"] & self.h_aire["baja"] & self.h_suelo["seca"], self.tiempo["largo"]))
        # 23
        rules.append(R(self.temperatura["alta"] & self.h_aire["alta"], self.frecuencia["media"]))
        # 24
        rules.append(R(self.viento["bajo"] & self.lluvia["baja"], self.frecuencia["media"]))
        # 25
        rules.append(R(self.temperatura["baja"] & self.h_suelo["moderada"], self.tiempo["corto"]))
        # 26
        rules.append(R(self.lluvia["media"] & self.viento["medio"], self.frecuencia["media"]))
        # 27
        rules.append(R(self.h_suelo["seca"] & self.h_aire["baja"] & self.lluvia["media"], self.tiempo["medio"]))
        # 28
        rules.append(R(self.h_suelo["moderada"] & self.h_aire["alta"] & self.lluvia["baja"], self.tiempo["medio"]))
        # 29
        rules.append(R(self.h_suelo["humeda"] & self.temperatura["alta"], self.frecuencia["media"]))
        # 30
        rules.append(R(self.h_suelo["seca"] & self.temperatura["alta"] & self.lluvia["baja"] & self.viento["alto"], (self.tiempo["largo"], self.frecuencia["alta"])) )
        # 31
        rules.append(R(self.temperatura["media"] & self.h_aire["media"] & self.lluvia["media"], (self.tiempo["medio"], self.frecuencia["media"])) )
        # 32
        rules.append(R(self.viento["alto"] & self.h_aire["baja"], self.tiempo["medio"]))
        # 33
        rules.append(R(self.viento["bajo"] & self.h_aire["alta"], self.frecuencia["baja"]))

        self._rules = rules
        self._ctrl = ctrl.ControlSystem(rules)
        self._sim = ctrl.ControlSystemSimulation(self._ctrl, flush_after_run=100)

    def _calcular_riego_interno(
        self,
        temperatura: float,
        humedad_suelo: float,
        probabilidad_lluvia: float,
        humedad_aire: float,
        velocidad_viento: float,
        ajuste_planta: float = 1.0,
    ) -> Tuple[float, float, Dict[str, float]]:
        """Calcula tiempo y frecuencia de riego (método interno).

        Returns:
            tuple: (tiempo_min, frecuencia, activaciones_por_regla)
        """
        # Set inputs
        self._sim.input["temperatura"] = float(temperatura)
        self._sim.input["humedad_suelo"] = float(humedad_suelo)
        self._sim.input["lluvia"] = float(probabilidad_lluvia)
        self._sim.input["humedad_aire"] = float(humedad_aire)
        self._sim.input["viento"] = float(velocidad_viento)

        self._sim.compute()

        tiempo = float(self._sim.output["tiempo"]) * float(ajuste_planta)
        frecuencia = float(self._sim.output["frecuencia"]) * (0.8 + 0.4 * (ajuste_planta))
        # clamp
        tiempo = max(0.0, min(60.0, tiempo))
        frecuencia = max(0.0, min(4.0, frecuencia))

        activ = self.obtener_activaciones_reglas(
            temperatura, humedad_suelo, probabilidad_lluvia, humedad_aire, velocidad_viento
        )
        return tiempo, frecuencia, activ

    # Wrapper solicitado por la especificación
    def calcular_riego(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Calcula riego a partir de un diccionario de entradas en español.

        Espera claves: temperatura, humedad_suelo, prob_lluvia, humedad_ambiente, velocidad_viento, planta_factor (opcional).
        Devuelve: {"tiempo": minutos, "frecuencia": veces_por_dia, "reglas_activadas": {R#: nivel}}
        """
        temp = float(inputs.get("temperatura", 0))
        hsuelo = float(inputs.get("humedad_suelo", 0))
        plluvia = float(inputs.get("prob_lluvia", inputs.get("lluvia", 0)))
        hamb = float(inputs.get("humedad_ambiente", inputs.get("humedad_aire", 0)))
        viento = float(inputs.get("velocidad_viento", inputs.get("viento", 0)))
        factor = float(inputs.get("planta_factor", inputs.get("ajuste_planta", 1.0)))

        t, f, act = self._calcular_riego_interno(
            temperatura=temp,
            humedad_suelo=hsuelo,
            probabilidad_lluvia=plluvia,
            humedad_aire=hamb,
            velocidad_viento=viento,
            ajuste_planta=factor,
        )
        return {"tiempo": t, "frecuencia": f, "reglas_activadas": act}

    def obtener_activaciones_reglas(
        self,
        temperature: float,
        soil_humidity: float,
        rain_probability: float,
        air_humidity: float,
        wind_speed: float,
    ) -> Dict[str, float]:
        """Devuelve el nivel de activación de cada regla para entradas dadas."""
        # Build antecedent membership degrees
        deg = {
            "t_baja": fuzz.interp_membership(TEMP_UNIVERSE, self.temperatura["baja"].mf, temperature),
            "t_media": fuzz.interp_membership(TEMP_UNIVERSE, self.temperatura["media"].mf, temperature),
            "t_alta": fuzz.interp_membership(TEMP_UNIVERSE, self.temperatura["alta"].mf, temperature),
            "s_seca": fuzz.interp_membership(SOIL_UNIVERSE, self.h_suelo["seca"].mf, soil_humidity),
            "s_moderada": fuzz.interp_membership(SOIL_UNIVERSE, self.h_suelo["moderada"].mf, soil_humidity),
            "s_humeda": fuzz.interp_membership(SOIL_UNIVERSE, self.h_suelo["humeda"].mf, soil_humidity),
            "l_baja": fuzz.interp_membership(RAIN_UNIVERSE, self.lluvia["baja"].mf, rain_probability),
            "l_media": fuzz.interp_membership(RAIN_UNIVERSE, self.lluvia["media"].mf, rain_probability),
            "l_alta": fuzz.interp_membership(RAIN_UNIVERSE, self.lluvia["alta"].mf, rain_probability),
            "a_baja": fuzz.interp_membership(AIRH_UNIVERSE, self.h_aire["baja"].mf, air_humidity),
            "a_media": fuzz.interp_membership(AIRH_UNIVERSE, self.h_aire["media"].mf, air_humidity),
            "a_alta": fuzz.interp_membership(AIRH_UNIVERSE, self.h_aire["alta"].mf, air_humidity),
            "v_bajo": fuzz.interp_membership(WIND_UNIVERSE, self.viento["bajo"].mf, wind_speed),
            "v_medio": fuzz.interp_membership(WIND_UNIVERSE, self.viento["medio"].mf, wind_speed),
            "v_alto": fuzz.interp_membership(WIND_UNIVERSE, self.viento["alto"].mf, wind_speed),
        }
        # Manually mirror rule firing strengths (min of antecedents used)
        activ: Dict[str, float] = {}
        def mn(*xs: float) -> float:
            return float(np.min(xs))
        idx = 1
        # Rebuild the same 33 rules' activation levels
        activ[f"R{idx}"] = mn(deg["s_seca"], deg["l_baja"]); idx+=1
        activ[f"R{idx}"] = deg["s_humeda"]; idx+=1
        activ[f"R{idx}"] = mn(deg["t_alta"], deg["s_seca"]); idx+=1
        activ[f"R{idx}"] = deg["l_alta"]; idx+=1
        activ[f"R{idx}"] = mn(deg["v_alto"], deg["t_alta"]); idx+=1
        activ[f"R{idx}"] = mn(deg["t_baja"], deg["a_alta"]); idx+=1
        activ[f"R{idx}"] = mn(deg["s_moderada"], deg["l_media"]); idx+=1
        activ[f"R{idx}"] = mn(deg["t_alta"], deg["a_baja"], deg["v_bajo"]); idx+=1
        activ[f"R{idx}"] = mn(deg["v_alto"], deg["l_baja"]); idx+=1
        activ[f"R{idx}"] = mn(deg["a_baja"], deg["s_seca"]); idx+=1
        activ[f"R{idx}"] = mn(deg["a_alta"], deg["l_media"]); idx+=1
        activ[f"R{idx}"] = mn(deg["t_media"], deg["s_moderada"]); idx+=1
        activ[f"R{idx}"] = mn(deg["t_media"], deg["l_baja"]); idx+=1
        activ[f"R{idx}"] = mn(deg["t_alta"], deg["v_medio"]); idx+=1
        activ[f"R{idx}"] = mn(deg["s_seca"], deg["v_alto"]); idx+=1
        activ[f"R{idx}"] = mn(deg["s_moderada"], deg["v_bajo"]); idx+=1
        activ[f"R{idx}"] = mn(deg["a_media"], deg["l_baja"]); idx+=1
        activ[f"R{idx}"] = mn(deg["t_baja"], deg["l_alta"]); idx+=1
        activ[f"R{idx}"] = mn(deg["a_baja"], deg["v_alto"]); idx+=1
        activ[f"R{idx}"] = mn(deg["s_humeda"], deg["l_alta"]); idx+=1
        activ[f"R{idx}"] = mn(deg["t_alta"], deg["l_media"], deg["v_alto"]); idx+=1
        activ[f"R{idx}"] = mn(deg["t_media"], deg["a_baja"], deg["s_seca"]); idx+=1
        activ[f"R{idx}"] = mn(deg["t_alta"], deg["a_alta"]); idx+=1
        activ[f"R{idx}"] = mn(deg["v_bajo"], deg["l_baja"]); idx+=1
        activ[f"R{idx}"] = mn(deg["t_baja"], deg["s_moderada"]); idx+=1
        activ[f"R{idx}"] = mn(deg["l_media"], deg["v_medio"]); idx+=1
        activ[f"R{idx}"] = mn(deg["s_seca"], deg["a_baja"], deg["l_media"]); idx+=1
        activ[f"R{idx}"] = mn(deg["s_moderada"], deg["a_alta"], deg["l_baja"]); idx+=1
        activ[f"R{idx}"] = mn(deg["s_humeda"], deg["t_alta"]); idx+=1
        activ[f"R{idx}"] = mn(deg["s_seca"], deg["t_alta"], deg["l_baja"], deg["v_alto"]); idx+=1
        activ[f"R{idx}"] = mn(deg["t_media"], deg["a_media"], deg["l_media"]); idx+=1
        activ[f"R{idx}"] = mn(deg["v_alto"], deg["a_baja"]); idx+=1
        activ[f"R{idx}"] = mn(deg["v_bajo"], deg["a_alta"]); idx+=1
        return activ

    def explain_decision(
        self,
        tiempo: float,
        frecuencia: float,
        activaciones: Dict[str, float],
    ) -> str:
        """Genera explicación en lenguaje natural resumida."""
        # top-3 reglas más activas
        top = sorted(activaciones.items(), key=lambda kv: kv[1], reverse=True)[:3]
        partes = [
            f"Tiempo recomendado: {tiempo:.1f} min; Frecuencia: {frecuencia:.2f} veces/día.",
            "Principales reglas activas: "
            + ", ".join([f"{k} ({v:.2f})" for k, v in top]),
        ]
        return " ".join(partes)

    # Métodos públicos en inglés para compatibilidad interna
    def get_rule_activations(
        self,
        temperature: float,
        soil_humidity: float,
        rain_probability: float,
        air_humidity: float,
        wind_speed: float,
    ) -> Dict[str, float]:
        return self.obtener_activaciones_reglas(temperature, soil_humidity, rain_probability, air_humidity, wind_speed)

    def calculate_irrigation(
        self,
        temperature: float,
        soil_humidity: float,
        rain_probability: float,
        air_humidity: float,
        wind_speed: float,
        ajuste_planta: float = 1.0,
    ) -> Tuple[float, float, Dict[str, float]]:
        return self._calcular_riego_interno(temperature, soil_humidity, rain_probability, air_humidity, wind_speed, ajuste_planta)
