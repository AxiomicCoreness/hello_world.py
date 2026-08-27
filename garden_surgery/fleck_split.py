from garden_surgery.theorems import PHI, PHI2
PHI4 = PHI2 * PHI2
PHI8 = PHI4 * PHI4
KAPPA_TR = 144.0 / PHI
DECAY_COEF = 144.0 * PHI4

def identities():
    return {
        "phi8": PHI8,
        "eleven_cubed": 11 ** 3,
        "kappa_144_over_phi": KAPPA_TR,
        "decay_144_phi4": DECAY_COEF,
        "declared_decay_987": 987.0,
        "decay_residual": DECAY_COEF - 987.0,
    }

def split():
    return {"identities": identities(), "fusion_canonical": 515, "hyperion_preserved": 516, "entry_9040_untouched": True}
