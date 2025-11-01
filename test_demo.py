from nucleo.motor_difuso import FuzzyIrrigationSystem

def peak_weighted_confidence(activations: dict, w_max: float = 0.7, alpha: float = 0.85) -> float:
    """
    Calcula confianza basada en activaciones de reglas fuzzy.
    """
    if not activations:
        return 0.75

    vals = list(activations.values())
    if not vals:
        return 0.75

    max_a = max(vals)
    mean_a = sum(vals) / len(vals)

    conf = w_max * (max_a ** alpha) + (1.0 - w_max) * (mean_a ** alpha)

    strong_rules = sum(1 for v in vals if v > 0.3)
    if strong_rules >= 3:
        conf = min(1.0, conf * 1.15)

    return min(1.0, float(conf))

sys = FuzzyIrrigationSystem()
result = sys.calcular_riego({
    'temperatura': 25,
    'humedad_suelo': 60,
    'prob_lluvia': 30,
    'humedad_ambiente': 50,
    'velocidad_viento': 10
})

# Recalcular confianza con el método del tablero
confianza_nueva = peak_weighted_confidence(result['reglas_activadas'], w_max=0.7, alpha=0.85)

print('Resultado original:', result)
print(f'Confianza recalculada: {confianza_nueva:.2f} ({confianza_nueva*100:.1f}%)')
print()
print('Reglas activadas (top 5):')
sorted_rules = sorted(result['reglas_activadas'].items(), key=lambda x: x[1], reverse=True)
for rule, activation in sorted_rules[:5]:
    print(f'{rule}: {activation:.3f}')
