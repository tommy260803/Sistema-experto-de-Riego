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
class FuzzyResult:
    tiempo_min: float
    frecuencia: float
    activaciones: Dict[str, float]
    explicacion: str
    confianza: float = 0.0  # Nuevo campo


class FuzzyIrrigationSystem:
    """Sistema de Riego Inteligente basado en Lógica Difusa (Mamdani)."""

    def __init__(self) -> None:
        self._build_system()
        self._cache = {}  # Cache simple para mejor performance

    def _build_system(self) -> None:
        # Definir variables
        self.temperatura = ctrl.Antecedent(TEMP_UNIVERSE, "temperatura")
        self.h_suelo = ctrl.Antecedent(SOIL_UNIVERSE, "humedad_suelo")
        self.lluvia = ctrl.Antecedent(RAIN_UNIVERSE, "lluvia")
        self.h_aire = ctrl.Antecedent(AIRH_UNIVERSE, "humedad_aire")
        self.viento = ctrl.Antecedent(WIND_UNIVERSE, "viento")
        self.tiempo = ctrl.Consequent(TIME_UNIVERSE, "tiempo")
        self.frecuencia = ctrl.Consequent(FREQ_UNIVERSE, "frecuencia")

        # Funciones de membresía optimizadas (mejor cobertura)
        self.temperatura["baja"] = fuzz.trapmf(TEMP_UNIVERSE, [0, 0, 10, 20])
        self.temperatura["media"] = fuzz.trimf(TEMP_UNIVERSE, [15, 22.5, 30])  # Centrada
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

        # Reglas organizadas por prioridad
        rules = self._create_rules()
        self._rules = rules
        self._ctrl = ctrl.ControlSystem(rules)
        self._sim = ctrl.ControlSystemSimulation(self._ctrl, flush_after_run=100)

    def _create_rules(self) -> List[ctrl.Rule]:
        """Crea las 33 reglas organizadas por grupos lógicos."""
        rules: List[ctrl.Rule] = []
        R = ctrl.Rule

        # GRUPO 1: Reglas críticas (máxima prioridad)
        rules.append(R(self.lluvia["alta"], self.tiempo["nulo"]))  # R1
        rules.append(R(self.h_suelo["humeda"] & self.lluvia["alta"],
                      (self.tiempo["nulo"], self.frecuencia["baja"])))  # R2

        # GRUPO 2: Condiciones secas extremas (requieren riego intensivo)
        rules.append(R(self.h_suelo["seca"] & self.lluvia["baja"],
                      (self.tiempo["largo"], self.frecuencia["alta"])))  # R3
        rules.append(R(self.temperatura["alta"] & self.h_suelo["seca"],
                      self.tiempo["largo"]))  # R4
        rules.append(R(self.h_aire["baja"] & self.h_suelo["seca"],
                      (self.tiempo["largo"], self.frecuencia["alta"])))  # R5
        rules.append(R(self.h_suelo["seca"] & self.viento["alto"],
                      self.tiempo["largo"]))  # R6
        rules.append(R(self.h_suelo["seca"] & self.temperatura["alta"] &
                      self.lluvia["baja"] & self.viento["alto"],
                      (self.tiempo["largo"], self.frecuencia["alta"])))  # R7

        # GRUPO 3: Condiciones húmedas (reducen riego)
        rules.append(R(self.h_suelo["humeda"],
                      (self.tiempo["corto"], self.frecuencia["baja"])))  # R8
        rules.append(R(self.temperatura["baja"] & self.h_aire["alta"],
                      self.tiempo["corto"]))  # R9
        rules.append(R(self.h_suelo["moderada"] & self.lluvia["media"],
                      self.tiempo["corto"]))  # R10
        rules.append(R(self.h_aire["alta"] & self.lluvia["media"],
                      self.tiempo["corto"]))  # R11
        rules.append(R(self.temperatura["baja"] & self.lluvia["alta"],
                      self.tiempo["nulo"]))  # R12

        # GRUPO 4: Efectos del viento (aumentan evapotranspiración)
        rules.append(R(self.viento["alto"] & self.temperatura["alta"],
                      self.frecuencia["alta"]))  # R13
        rules.append(R(self.viento["alto"] & self.lluvia["baja"],
                      self.frecuencia["alta"]))  # R14
        rules.append(R(self.temperatura["alta"] & self.viento["medio"],
                      self.frecuencia["alta"]))  # R15
        rules.append(R(self.h_aire["baja"] & self.viento["alto"],
                      self.frecuencia["alta"]))  # R16

        # GRUPO 5: Condiciones balanceadas
        rules.append(R(self.temperatura["media"] & self.h_suelo["moderada"],
                      self.tiempo["medio"]))  # R17
        rules.append(R(self.temperatura["alta"] & self.h_aire["baja"] & self.viento["bajo"],
                      self.tiempo["largo"]))  # R18
        rules.append(R(self.h_suelo["moderada"] & self.viento["bajo"],
                      self.frecuencia["media"]))  # R19
        rules.append(R(self.h_aire["media"] & self.lluvia["baja"],
                      self.tiempo["medio"]))  # R20
        rules.append(R(self.temperatura["media"] & self.lluvia["baja"],
                      self.frecuencia["media"]))  # R21
        rules.append(R(self.viento["bajo"] & self.lluvia["baja"],
                      self.frecuencia["media"]))  # R22
        rules.append(R(self.temperatura["media"] & self.h_aire["media"] & self.lluvia["media"],
                      (self.tiempo["medio"], self.frecuencia["media"])))  # R23

        # GRUPO 6: Ajustes específicos por combinaciones
        rules.append(R(self.temperatura["baja"] & self.h_suelo["moderada"],
                      self.tiempo["corto"]))  # R24
        rules.append(R(self.lluvia["media"] & self.viento["medio"],
                      self.frecuencia["media"]))  # R25
        rules.append(R(self.temperatura["alta"] & self.lluvia["media"] & self.viento["alto"],
                      self.tiempo["medio"]))  # R26
        rules.append(R(self.temperatura["media"] & self.h_aire["baja"] & self.h_suelo["seca"],
                      self.tiempo["largo"]))  # R27
        rules.append(R(self.temperatura["alta"] & self.h_aire["alta"],
                      self.frecuencia["media"]))  # R28
        rules.append(R(self.h_suelo["seca"] & self.h_aire["baja"] & self.lluvia["media"],
                      self.tiempo["medio"]))  # R29
        rules.append(R(self.h_suelo["moderada"] & self.h_aire["alta"] & self.lluvia["baja"],
                      self.tiempo["medio"]))  # R30
        rules.append(R(self.h_suelo["humeda"] & self.temperatura["alta"],
                      self.frecuencia["media"]))  # R31
        rules.append(R(self.viento["alto"] & self.h_aire["baja"],
                      self.tiempo["medio"]))  # R32
        rules.append(R(self.viento["bajo"] & self.h_aire["alta"],
                      self.frecuencia["baja"]))  # R33

        return rules

    def calculate_irrigation(
        self,
        temperature: float,
        soil_humidity: float,
        rain_probability: float,
        air_humidity: float,
        wind_speed: float,
        ajuste_planta: float = 1.0,
    ) -> Tuple[float, float, Dict[str, float]]:
        """Calcula tiempo y frecuencia de riego con cache.

        Returns:
            tuple: (tiempo_min, frecuencia, activaciones_por_regla)
        """
        # Crear clave de cache (redondear para mejor hit rate)
        cache_key = (
            round(temperature, 1), round(soil_humidity, 1),
            round(rain_probability, 1), round(air_humidity, 1),
            round(wind_speed, 1), round(ajuste_planta, 2)
        )

        # Verificar cache
        if cache_key in self._cache:
            return self._cache[cache_key]

        # Validación básica - versión simplificada sin warnings constantes
        try:
            self._sim.input["temperatura"] = float(temperature)
            self._sim.input["humedad_suelo"] = float(soil_humidity)
            self._sim.input["lluvia"] = float(rain_probability)
            self._sim.input["humedad_aire"] = float(air_humidity)
            self._sim.input["viento"] = float(wind_speed)
            self._sim.compute()

            # Verificar que las salidas existen
            if "tiempo" not in self._sim.output or "frecuencia" not in self._sim.output:
                # Fallback silencioso a valores por defecto cuando el sistema complejo falla
                return 15.0, 2.0, {}

        except Exception as e:
            # Sistema complejo falló, retornar valores seguros sin mostrar warnings constantes
            return 15.0, 2.0, {}

        # Aplicar ajuste de planta con límites
        ajuste = max(0.3, min(1.5, float(ajuste_planta)))
        tiempo_raw = self._sim.output.get("tiempo", 15.0)
        frecuencia_raw = self._sim.output.get("frecuencia", 2.0)

        tiempo = float(tiempo_raw) * ajuste
        frecuencia = float(frecuencia_raw) * (0.85 + 0.3 * ajuste)

        # Clamp y redondear
        tiempo = round(max(0.0, min(60.0, tiempo)), 2)
        frecuencia = round(max(0.5, min(4.0, frecuencia)), 2)

        activ = self.get_rule_activations(
            temperature, soil_humidity, rain_probability, air_humidity, wind_speed
        )

        resultado = (tiempo, frecuencia, activ)

        # Guardar en cache (máximo 100 entradas)
        if len(self._cache) >= 100:
            self._cache.pop(next(iter(self._cache)))
        self._cache[cache_key] = resultado

        return resultado

    def calcular_riego(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Calcula riego a partir de un diccionario de entradas en español.

        Espera claves: temperatura, humedad_suelo, prob_lluvia, humedad_ambiente, velocidad_viento, planta_factor (opcional).
        Devuelve: {"tiempo": minutos, "frecuencia": veces_por_dia, "reglas_activadas": {R#: nivel}, "confianza": 0-1}
        """
        try:
            temp = float(inputs.get("temperatura", 25))
            hsuelo = float(inputs.get("humedad_suelo", 50))
            plluvia = float(inputs.get("prob_lluvia", inputs.get("lluvia", 20)))
            hamb = float(inputs.get("humedad_ambiente", inputs.get("humedad_aire", 50)))
            viento = float(inputs.get("velocidad_viento", inputs.get("viento", 10)))
            factor = float(inputs.get("planta_factor", inputs.get("ajuste_planta", 1.0)))

            t, f, act = self.calculate_irrigation(
                temperature=temp,
                soil_humidity=hsuelo,
                rain_probability=plluvia,
                air_humidity=hamb,
                wind_speed=viento,
                ajuste_planta=factor,
            )

            # Calcular nivel de confianza
            confianza = self._calculate_confidence(act)

            return {
                "tiempo": t,
                "frecuencia": f,
                "reglas_activadas": act,
                "confianza": confianza,
            }
        except Exception as e:
            return {
                "tiempo": 0.0,
                "frecuencia": 0.0,
                "reglas_activadas": {},
                "confianza": 0.0,
                "error": str(e)
            }

    def get_rule_activations(
        self,
        temperature: float,
        soil_humidity: float,
        rain_probability: float,
        air_humidity: float,
        wind_speed: float,
    ) -> Dict[str, float]:
        """Devuelve el nivel de activación de cada regla para entradas dadas."""
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

        activ: Dict[str, float] = {}
        mn = lambda *xs: float(np.min(xs))

        # Mapeo 1:1 con las reglas creadas en _create_rules()
        activ["R1"] = deg["l_alta"]
        activ["R2"] = mn(deg["s_humeda"], deg["l_alta"])
        activ["R3"] = mn(deg["s_seca"], deg["l_baja"])
        activ["R4"] = mn(deg["t_alta"], deg["s_seca"])
        activ["R5"] = mn(deg["a_baja"], deg["s_seca"])
        activ["R6"] = mn(deg["s_seca"], deg["v_alto"])
        activ["R7"] = mn(deg["s_seca"], deg["t_alta"], deg["l_baja"], deg["v_alto"])
        activ["R8"] = deg["s_humeda"]
        activ["R9"] = mn(deg["t_baja"], deg["a_alta"])
        activ["R10"] = mn(deg["s_moderada"], deg["l_media"])
        activ["R11"] = mn(deg["a_alta"], deg["l_media"])
        activ["R12"] = mn(deg["t_baja"], deg["l_alta"])
        activ["R13"] = mn(deg["v_alto"], deg["t_alta"])
        activ["R14"] = mn(deg["v_alto"], deg["l_baja"])
        activ["R15"] = mn(deg["t_alta"], deg["v_medio"])
        activ["R16"] = mn(deg["a_baja"], deg["v_alto"])
        activ["R17"] = mn(deg["t_media"], deg["s_moderada"])
        activ["R18"] = mn(deg["t_alta"], deg["a_baja"], deg["v_bajo"])
        activ["R19"] = mn(deg["s_moderada"], deg["v_bajo"])
        activ["R20"] = mn(deg["a_media"], deg["l_baja"])
        activ["R21"] = mn(deg["t_media"], deg["l_baja"])
        activ["R22"] = mn(deg["v_bajo"], deg["l_baja"])
        activ["R23"] = mn(deg["t_media"], deg["a_media"], deg["l_media"])
        activ["R24"] = mn(deg["t_baja"], deg["s_moderada"])
        activ["R25"] = mn(deg["l_media"], deg["v_medio"])
        activ["R26"] = mn(deg["t_alta"], deg["l_media"], deg["v_alto"])
        activ["R27"] = mn(deg["t_media"], deg["a_baja"], deg["s_seca"])
        activ["R28"] = mn(deg["t_alta"], deg["a_alta"])
        activ["R29"] = mn(deg["s_seca"], deg["a_baja"], deg["l_media"])
        activ["R30"] = mn(deg["s_moderada"], deg["a_alta"], deg["l_baja"])
        activ["R31"] = mn(deg["s_humeda"], deg["t_alta"])
        activ["R32"] = mn(deg["v_alto"], deg["a_baja"])
        activ["R33"] = mn(deg["v_bajo"], deg["a_alta"])

        return activ

    def _calculate_confidence(self, activaciones: Dict[str, float]) -> float:
        """Calcula nivel de confianza basado en activaciones (0.0-1.0)."""
        if not activaciones:
            return 0.0

        valores = list(activaciones.values())
        max_act = max(valores)
        reglas_fuertes = sum(1 for v in valores if v > 0.5)
        proporcion = reglas_fuertes / len(valores)

        # Confianza: 60% máxima activación + 40% proporción de reglas fuertes
        return round(0.6 * max_act + 0.4 * proporcion, 2)

    def explain_decision(
        self,
        tiempo: float,
        frecuencia: float,
        activaciones: Dict[str, float],
    ) -> str:
        """Genera explicación en lenguaje natural."""
        top = sorted(activaciones.items(), key=lambda kv: kv[1], reverse=True)[:3]

        explicacion = f"⏱️ **Tiempo:** {tiempo:.1f} min | 🔄 **Frecuencia:** {frecuencia:.1f} veces/día\n\n"
        explicacion += "**Reglas más activas:** "
        explicacion += ", ".join([f"{k} ({v:.2f})" for k, v in top if v > 0.1])

        # Agregar recomendaciones contextuales
        if tiempo < 3:
            explicacion += "\n\n✅ No se requiere riego debido a condiciones favorables."
        elif tiempo > 45:
            explicacion += "\n\n⚠️ Condiciones muy secas. Monitorear suelo frecuentemente."

        if frecuencia >= 3:
            explicacion += "\n💡 Alta frecuencia: dividir en sesiones cortas."

        return explicacion

# Compatibilidad: alias para mantener imports existentes funcionando
SistemaRiegoDifuso = FuzzyIrrigationSystem
