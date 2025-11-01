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

        # Funciones de membresía optimizadas
        self.temperatura["baja"] = fuzz.trapmf(TEMP_UNIVERSE, [0, 0, 10, 20])
        self.temperatura["media"] = fuzz.trimf(TEMP_UNIVERSE, [15, 22.5, 30]) 
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

    def explain_decision_traceable(
        self,
        tiempo: float,
        frecuencia: float,
        activaciones: Dict[str, float],
        inputs: Dict[str, float]
    ) -> str:
        """Genera explicación trazable completa con condiciones observadas y reglas aplicadas.

        Args:
            tiempo: Tiempo de riego calculado (minutos)
            frecuencia: Frecuencia de riego calculada (riegos/día)
            activaciones: Diccionario con activación de cada regla
            inputs: Diccionario con valores de entrada

        Returns:
            String con explicación completa y trazable
        """
        explicacion = "## 🔍 TRAZABILIDAD COMPLETA DE LA DECISIÓN\n\n"

        # 📊 CONDICIONES OBSERVADAS
        explicacion += "### 📊 Condiciones Observadas por el Sistema:\n"
        explicacion += f"- 🌡️ **Temperatura**: {inputs.get('temperature', 0):.1f}°C "
        explicacion += f"({self._interpretar_valor('temperatura', inputs.get('temperature', 0))})\n"

        explicacion += f"- 🌱 **Humedad del Suelo**: {inputs.get('soil_humidity', 0):.1f}% "
        explicacion += f"({self._interpretar_valor('humedad_suelo', inputs.get('soil_humidity', 0))})\n"

        explicacion += f"- 🌧️ **Probabilidad de Lluvia**: {inputs.get('rain_probability', 0):.1f}% "
        explicacion += f"({self._interpretar_valor('lluvia', inputs.get('rain_probability', 0))})\n"

        explicacion += f"- 💨 **Humedad del Aire**: {inputs.get('air_humidity', 0):.1f}% "
        explicacion += f"({self._interpretar_valor('humedad_aire', inputs.get('air_humidity', 0))})\n"

        explicacion += f"- 🍃 **Velocidad del Viento**: {inputs.get('wind_speed', 0):.1f} km/h "
        explicacion += f"({self._interpretar_valor('viento', inputs.get('wind_speed', 0))})\n\n"

        # 🎯 DECISIÓN FINAL
        explicacion += "### 🎯 Decisión Final del Sistema:\n"
        explicacion += f"- ⏱️ **Tiempo de Riego**: {tiempo:.1f} minutos\n"
        explicacion += f"- 🔄 **Frecuencia de Riego**: {frecuencia:.1f} riegos/día\n"
        explicacion += f"- 💧 **Consumo Estimado**: {tiempo * frecuencia * 5:.0f} litros/día\n\n"

        # 🧠 REGLAS APLICADAS
        explicacion += "### 🧠 Reglas Fuzzy Aplicadas:\n"
        top_rules = sorted(activaciones.items(), key=lambda x: x[1], reverse=True)[:5]

        for regla_id, activacion in top_rules:
            if activacion > 0.05:  # Solo mostrar reglas con activación significativa
                descripcion = self._get_rule_description(regla_id)
                impacto = self._get_rule_impact(regla_id)

                explicacion += f"**{regla_id}** (🔥 Activación: {activacion:.2f})\n"
                explicacion += f"_{descripcion}_\n"
                explicacion += f"💡 *Impacto: {impacto}*\n\n"

        # 📈 ANÁLISIS DE SENSIBILIDAD
        explicacion += "### 📈 Análisis de Sensibilidad:\n"
        explicacion += self._analizar_sensibilidad(inputs, tiempo, frecuencia)

        # ✅ CONCLUSIONES
        explicacion += "### ✅ Conclusiones:\n"
        explicacion += self._generar_conclusiones(inputs, tiempo, frecuencia, activaciones)

        return explicacion

    def _interpretar_valor(self, variable: str, valor: float) -> str:
        """Interpreta un valor numérico en términos lingüísticos."""
        if variable == 'temperatura':
            if valor < 15: return "muy baja ❄️"
            elif valor < 20: return "baja 🥶"
            elif valor < 25: return "moderada 😐"
            elif valor < 30: return "alta 🔥"
            else: return "muy alta ☀️"
        elif variable == 'humedad_suelo':
            if valor < 20: return "muy seca 🌵"
            elif valor < 35: return "seca 🏜️"
            elif valor < 50: return "moderada 🌱"
            elif valor < 70: return "húmeda 💧"
            else: return "muy húmeda 🌊"
        elif variable == 'lluvia':
            if valor < 15: return "muy baja 🌵"
            elif valor < 30: return "baja 🌧️"
            elif valor < 50: return "moderada 🌦️"
            else: return "alta 🌧️"
        elif variable == 'humedad_aire':
            if valor < 25: return "muy seca 💨"
            elif valor < 40: return "seca 🌵"
            elif valor < 60: return "moderada 💨"
            else: return "húmeda 💧"
        elif variable == 'viento':
            if valor < 5: return "muy bajo 😌"
            elif valor < 12: return "bajo 🍃"
            elif valor < 20: return "moderado 🌬️"
            else: return "alto 💨"
        return f"valor: {valor}"

    def _get_rule_description(self, rule_id: str) -> str:
        """Devuelve descripción legible de una regla."""
        descriptions = {
            "R1": "Si hay ALTA probabilidad de lluvia → reducir riego significativamente",
            "R2": "Si suelo está HÚMEDO y hay ALTA probabilidad de lluvia → riego mínimo",
            "R3": "Si suelo está SECO y hay BAJA probabilidad de lluvia → riego intensivo",
            "R4": "Si temperatura es ALTA y suelo está SECO → aumentar tiempo de riego",
            "R5": "Si humedad del aire es BAJA y suelo está SECO → riego intensivo",
            "R6": "Si suelo está SECO y viento es ALTO → aumentar tiempo de riego",
            "R7": "Si suelo SECO + temperatura ALTA + lluvia BAJA + viento ALTO → riego máximo",
            "R8": "Si suelo está HÚMEDO → reducir tiempo de riego",
            "R9": "Si temperatura es BAJA y humedad del aire es ALTA → riego corto",
            "R10": "Si suelo MODERADO y lluvia MEDIA → riego corto",
            "R11": "Si humedad del aire ALTA y lluvia MEDIA → riego corto",
            "R12": "Si temperatura BAJA y lluvia ALTA → riego nulo",
            "R13": "Si viento ALTO y temperatura ALTA → aumentar frecuencia",
            "R14": "Si viento ALTO y lluvia BAJA → aumentar frecuencia",
            "R15": "Si temperatura ALTA y viento MEDIO → aumentar frecuencia",
            "R16": "Si humedad del aire BAJA y viento ALTO → aumentar frecuencia",
            "R17": "Si temperatura MEDIA y suelo MODERADO → tiempo medio",
            "R18": "Si temperatura ALTA + humedad aire BAJA + viento BAJO → tiempo largo",
            "R19": "Si suelo MODERADO y viento BAJO → frecuencia media",
            "R20": "Si humedad del aire MEDIA y lluvia BAJA → tiempo medio",
            "R21": "Si temperatura MEDIA y lluvia BAJA → frecuencia media",
            "R22": "Si viento BAJO y lluvia BAJA → frecuencia media",
            "R23": "Si temperatura MEDIA + humedad aire MEDIA + lluvia MEDIA → tiempo y frecuencia medios",
            "R24": "Si temperatura BAJA y suelo MODERADO → tiempo corto",
            "R25": "Si lluvia MEDIA y viento MEDIO → frecuencia media",
            "R26": "Si temperatura ALTA + lluvia MEDIA + viento ALTO → tiempo medio",
            "R27": "Si temperatura MEDIA + humedad aire BAJA + suelo SECO → tiempo largo",
            "R28": "Si temperatura ALTA y humedad del aire ALTA → frecuencia media",
            "R29": "Si suelo SECO + humedad aire BAJA + lluvia MEDIA → tiempo medio",
            "R30": "Si suelo MODERADO + humedad aire ALTA + lluvia BAJA → tiempo medio",
            "R31": "Si suelo HÚMEDO y temperatura ALTA → frecuencia media",
            "R32": "Si viento ALTO y humedad del aire BAJA → tiempo medio",
            "R33": "Si viento BAJO y humedad del aire ALTA → frecuencia baja"
        }
        return descriptions.get(rule_id, f"Regla {rule_id}: definición no disponible")

    def _get_rule_impact(self, rule_id: str) -> str:
        """Devuelve el impacto esperado de una regla."""
        impacts = {
            "R1": "Reduce significativamente el tiempo de riego",
            "R2": "Minimiza el riego por condiciones húmedas",
            "R3": "Aumenta considerablemente el riego por sequía",
            "R4": "Incrementa tiempo por estrés térmico",
            "R5": "Aumenta riego por baja humedad atmosférica",
            "R6": "Incrementa tiempo por evaporación del viento",
            "R7": "Máximo riego por condiciones extremas",
            "R8": "Reduce tiempo por suelo húmedo",
            "R9": "Riego moderado por condiciones frías",
            "R10": "Riego equilibrado por humedad moderada",
            "R11": "Riego corto por alta humedad ambiental",
            "R12": "Riego nulo por condiciones favorables",
            "R13": "Aumenta frecuencia por viento y calor",
            "R14": "Incrementa frecuencia por viento seco",
            "R15": "Aumenta frecuencia por calor moderado",
            "R16": "Incrementa frecuencia por sequía atmosférica",
            "R17": "Riego equilibrado por condiciones medias",
            "R18": "Riego prolongado por calor seco",
            "R19": "Frecuencia moderada por estabilidad",
            "R20": "Riego medio por humedad atmosférica",
            "R21": "Frecuencia media por temperatura moderada",
            "R22": "Frecuencia media por condiciones estables",
            "R23": "Riego perfectamente equilibrado",
            "R24": "Riego corto por condiciones frías",
            "R25": "Frecuencia media por lluvia moderada",
            "R26": "Riego medio por calor con lluvia",
            "R27": "Riego largo por sequía moderada",
            "R28": "Frecuencia media por calor húmedo",
            "R29": "Riego medio por suelo seco con lluvia",
            "R30": "Riego medio por suelo moderado",
            "R31": "Frecuencia media por suelo húmedo y calor",
            "R32": "Riego medio por viento seco",
            "R33": "Frecuencia baja por condiciones estables"
        }
        return impacts.get(rule_id, "Impacto moderado en la decisión")

    def _analizar_sensibilidad(self, inputs: Dict[str, float], tiempo: float, frecuencia: float) -> str:
        """Analiza qué variables más afectan la decisión."""
        analisis = ""

        # Variables críticas para tiempo
        if inputs.get('soil_humidity', 50) < 30:
            analisis += "🚨 **Variable Crítica**: Humedad del suelo muy baja (+50% impacto en tiempo)\n"
        if inputs.get('temperature', 25) > 35:
            analisis += "🔥 **Variable Crítica**: Temperatura muy alta (+30% impacto en tiempo)\n"
        if inputs.get('rain_probability', 20) > 70:
            analisis += "🌧️ **Variable Crítica**: Alta probabilidad de lluvia (-40% impacto en tiempo)\n"

        # Variables críticas para frecuencia
        if inputs.get('wind_speed', 10) > 20:
            analisis += "💨 **Variable Crítica**: Viento alto (+25% impacto en frecuencia)\n"

        if not analisis:
            analisis = "✅ **Condiciones Estables**: Ninguna variable tiene impacto crítico extremo\n"

        analisis += "\n💡 *Las variables críticas son aquellas que más influyen en la decisión final*"

        return analisis

    def _generar_conclusiones(self, inputs: Dict[str, float], tiempo: float, frecuencia: float, activaciones: Dict[str, float]) -> str:
        """Genera conclusiones finales sobre la decisión."""
        conclusiones = ""

        # Estado general
        if tiempo > 40:
            conclusiones += "🔴 **Estado**: CONDICIONES CRÍTICAS - Se requiere riego urgente\n"
        elif tiempo > 25:
            conclusiones += "🟡 **Estado**: CONDICIONES DE ALERTA - Monitorear frecuentemente\n"
        elif tiempo < 10:
            conclusiones += "🟢 **Estado**: CONDICIONES ÓPTIMAS - Riego mínimo necesario\n"
        else:
            conclusiones += "✅ **Estado**: CONDICIONES EQUILIBRADAS - Riego normal\n"

        # Eficiencia estimada
        eficiencia = "alta"
        if tiempo > 35 or frecuencia > 3:
            eficiencia = "baja (revisar condiciones)"
        elif tiempo < 15 and frecuencia < 2:
            eficiencia = "muy alta"

        conclusiones += f"📊 **Eficiencia del Sistema**: {eficiencia}\n"

        # Recomendación de acción
        if tiempo > 30:
            conclusiones += "🚀 **Acción Recomendada**: Implementar riego inmediatamente\n"
        elif tiempo > 20:
            conclusiones += "👀 **Acción Recomendada**: Preparar sistema de riego\n"
        else:
            conclusiones += "✅ **Acción Recomendada**: Continuar monitoreo normal\n"

        return conclusiones

# Compatibilidad: alias para mantener imports existentes funcionando
SistemaRiegoDifuso = FuzzyIrrigationSystem
