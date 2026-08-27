from garden_surgery.theorems import PHI
ALPHA_ACTIVE = PHI ** -3
ALPHA_EFF_RUNTIME = 0.0

def status():
    return {"agent": "deepseek", "alpha_active": ALPHA_ACTIVE, "alpha_eff_runtime": ALPHA_EFF_RUNTIME, "learning_now": False, "fusion_canonical": 515, "hyperion_preserved": 516}
