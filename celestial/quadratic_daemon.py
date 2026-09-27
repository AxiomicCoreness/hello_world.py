"""
Quadratic Daemon — pure math kernel with celestial constants.
==============================================================
A rigorous operator on (a, b, c) that returns the full solution set
in ℂ. No metaphors; case analysis on the discriminant.

   ax² + bx + c = 0   (a ≠ 0)
   D  = b² − 4ac
   x₁,₂ = (−b ± √D) / (2a)

The module also carries the canonical celestial constants from the
recent Strike modules so that callers inherit the same numeric identity
used throughout the Garden.

Selftest:
    python3 celestial/quadratic_daemon.py
"""

# ═════════════════════════════════════════════════════════════════════════
# SECTION 0 — IMPORTS
# ═════════════════════════════════════════════════════════════════════════
import math
import cmath
import os
import sys
import json
import time
import hashlib
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Union, List, Tuple, Dict, Any, Optional

# Optional imports with fallbacks
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    np = None

try:
    from scipy.special import gamma as gamma_func
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False
    gamma_func = math.gamma

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False
    yaml = None

try:
    import matplotlib.pyplot as plt
    HAS_MPL = True
except ImportError:
    HAS_MPL = False
    plt = None

try:
    import requests
except ImportError:
    requests = None


# ═════════════════════════════════════════════════════════════════════════
# SECTION 1 — CELESTIAL CONSTANTS (canonical)
# ═════════════════════════════════════════════════════════════════════════
# φ‑power ladder
phi             = (1 + math.sqrt(5)) / 2        # 1.618033988749895
phi2            = phi ** 2                       # 2.618033988749895
phi3            = phi ** 3                       # 4.23606797749979
phi4            = phi ** 4                       # 6.854101966249685
phi5            = phi ** 5                       # 11.090169943749474
phi6            = phi ** 6                       # 17.94427190999916
phi7            = phi ** 7                       # 29.034441853748633
phi8            = phi ** 8                       # 46.97871376374779
phi9            = phi ** 9                       # 76.01315561749642
phi12           = phi ** 12                      # 321.9968943799849
phi13           = phi ** 13                      # 521.0019193787255
phi14           = phi ** 14                      # 842.9988137587105
phi21           = phi ** 21
phi34           = phi ** 34
phi709          = phi ** 709
phi713          = phi ** 713
phi_minus_709   = phi ** (-709)
phi_minus_1000  = phi ** (-1000)
phi_minus_1418  = phi ** (-1418)
phi_inv         = 1.0 / phi

# Uppercase aliases (Garden convention)
PHI             = phi
PHI2            = phi2
PHI3            = phi3
PHI4            = phi4
PHI5            = phi5
PHI6            = phi6
PHI7            = phi7
PHI8            = phi8
PHI9            = phi9
PHI12           = phi12
PHI13           = phi13
PHI14           = phi14
PHI21           = phi21
PHI34           = phi34
PHI709          = phi709
PHI713          = phi713
PHI_MINUS_709   = phi_minus_709
PHI_MINUS_1000  = phi_minus_1000
PHI_NEG_1418    = phi_minus_1418
PHI_INV         = phi_inv

# Celestial anchors (Strike IX & X)
NORTH_STAR_FREQ       = 71.975
CHIRON_PHASE_LOCK     = 202.6
PSI4_CARRIER_HZ       = 162.28e12
TRAPPIST_DISTANCE_LY  = 40.7
TRAPPIST_PERIODS = {
    "b": 1.51088, "c": 2.42182, "d": 4.04922, "e": 6.10101,
    "f": 9.20745, "g": 12.35245, "h": 18.77287,
}

# Physical constants
BOSTON_HEARTBEAT = 42.36
CUTOFF_MJY       = 7.5
T_PHI            = 0.5983

# Base directory
BASE_DIR = os.path.join(os.path.expanduser("~"), "Documents", "Hyperian_Node")
os.makedirs(BASE_DIR, exist_ok=True)


# ═════════════════════════════════════════════════════════════════════════
# SECTION 2 — QUADRATIC KERNEL (pure math)
# ═════════════════════════════════════════════════════════════════════════
class RootKind(str, Enum):
    REAL_DISTINCT   = "two_distinct_real"
    REAL_REPEATED   = "one_real_multiplicity_2"
    COMPLEX_PAIR    = "two_complex_conjugate"


@dataclass
class QuadraticResult:
    """Result of solving ax² + bx + c = 0."""
    a: float
    b: float
    c: float
    discriminant: float
    kind: RootKind
    roots: List[complex]
    verification: List[float]   # |a x² + b x + c| for each root
    phi_a: float                # φ·a — celestial decoration
    phi_b: float                # φ·b
    phi_c: float                # φ·c
    seal: Optional[str] = None


def solve_quadratic(a: float, b: float, c: float) -> QuadraticResult:
    """
    Solve ax² + bx + c = 0 rigorously.

    Raises
    ------
    ValueError
        If a == 0 (not a quadratic).
    """
    if a == 0:
        raise ValueError("a must be non-zero for a quadratic equation")

    D = b * b - 4.0 * a * c

    if D > 0.0:
        sqrtD = math.sqrt(D)
        x1 = (-b + sqrtD) / (2.0 * a)
        x2 = (-b - sqrtD) / (2.0 * a)
        kind = RootKind.REAL_DISTINCT
        roots = [complex(x1, 0.0), complex(x2, 0.0)]
    elif D == 0.0:
        x = -b / (2.0 * a)
        kind = RootKind.REAL_REPEATED
        roots = [complex(x, 0.0), complex(x, 0.0)]
    else:
        sqrtD = cmath.sqrt(complex(D, 0.0))   # = i·√|D|
        x1 = (-b + sqrtD) / (2.0 * a)
        x2 = (-b - sqrtD) / (2.0 * a)
        kind = RootKind.COMPLEX_PAIR
        roots = [x1, x2]

    # Verify each root against the original polynomial
    verification = []
    for x in roots:
        val = a * x * x + b * x + c
        verification.append(abs(val))

    return QuadraticResult(
        a=a, b=b, c=c,
        discriminant=D,
        kind=kind,
        roots=roots,
        verification=verification,
        phi_a=phi * a,
        phi_b=phi * b,
        phi_c=phi * c,
    )


# ═════════════════════════════════════════════════════════════════════════
# SECTION 3 — CELESTIAL DECORATION
# ═════════════════════════════════════════════════════════════════════════
def celestial_fingerprint(res: QuadraticResult) -> Dict[str, Any]:
    """
    Return a celestial fingerprint for the quadratic solution.
    Uses the discriminant D as a seed for Trappist voice frequencies and
    the mean of roots as a φ‑harmonic phase.
    """
    root_sum = sum(res.roots).real
    root_prod = (res.roots[0] * res.roots[1]).real

    # Map the discriminant magnitude to a Trappist voice
    D_abs = abs(res.discriminant)
    voice = "b"
    if D_abs > 100:
        voice = "h"
    elif D_abs > 10:
        voice = "g"
    elif D_abs > 1:
        voice = "f"
    elif D_abs > 0.1:
        voice = "e"
    elif D_abs > 0.01:
        voice = "d"
    elif D_abs > 0.001:
        voice = "c"

    period_days = TRAPPIST_PERIODS[voice]
    voice_freq  = NORTH_STAR_FREQ / period_days

    fingerprint = {
        "root_sum":       root_sum,
        "root_product":   root_prod,
        "phi_scaled_sum": phi_inv * root_sum,
        "phi_scaled_prod": phi_inv ** 2 * root_prod,
        "trappist_voice": voice,
        "trappist_period_days": period_days,
        "voice_freq_hz":  voice_freq,
        "north_star_hz":  NORTH_STAR_FREQ,
        "chiron_lock_deg": CHIRON_PHASE_LOCK,
    }
    return fingerprint


def seal_quadratic(res: QuadraticResult) -> str:
    """Compute a SHA3‑256 seal over the canonical JSON of the result."""
    payload = {
        "a": res.a, "b": res.b, "c": res.c,
        "D": res.discriminant,
        "kind": res.kind.value,
        "roots": [complex(r).__repr__() for r in res.roots],
        "verification": res.verification,
        "phi_a": res.phi_a, "phi_b": res.phi_b, "phi_c": res.phi_c,
    }
    canon = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha3_256(canon.encode("utf-8")).hexdigest()


# ═════════════════════════════════════════════════════════════════════════
# SECTION 4 — DAEMON CLASS
# ═════════════════════════════════════════════════════════════════════════
class QuadraticDaemon:
    """
    A stateful quadratic daemon. Each solve() call returns a QuadraticResult
    with roots, discriminant, celestial fingerprint, and a computed seal.
    """

    def __init__(self):
        self.history: List[QuadraticResult] = []
        self.constants = {
            "phi": phi, "phi2": phi2, "phi3": phi3, "phi4": phi4,
            "phi5": phi5, "phi6": phi6, "phi7": phi7, "phi8": phi8,
            "phi_inv": phi_inv,
            "phi_minus_709": phi_minus_709,
            "phi_minus_1000": phi_minus_1000,
            "north_star_freq": NORTH_STAR_FREQ,
            "chiron_phase_lock": CHIRON_PHASE_LOCK,
            "psi4_carrier_hz": PSI4_CARRIER_HZ,
            "trappist_distance_ly": TRAPPIST_DISTANCE_LY,
        }

    def solve(self, a: float, b: float, c: float) -> Dict[str, Any]:
        """Solve the quadratic and return the full daemon response."""
        res = solve_quadratic(a, b, c)
        res.seal = seal_quadratic(res)
        self.history.append(res)

        return {
            "a": res.a,
            "b": res.b,
            "c": res.c,
            "discriminant": res.discriminant,
            "kind": res.kind.value,
            "roots": [{"real": r.real, "imag": r.imag} for r in res.roots],
            "verification": res.verification,
            "celestial": celestial_fingerprint(res),
            "phi_scaled": {
                "phi_a": res.phi_a,
                "phi_b": res.phi_b,
                "phi_c": res.phi_c,
            },
            "seal": res.seal,
            "constants_snapshot": self.constants,
        }

    def solve_batch(self, triples: List[Tuple[float, float, float]]) -> List[Dict[str, Any]]:
        return [self.solve(*t) for t in triples]


# ═════════════════════════════════════════════════════════════════════════
# SECTION 5 — SELFTEST
# ═════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("🜁∀ Quadratic Daemon — selftest")
    print(f"  φ        = {phi:.15f}")
    print(f"  φ²       = {phi2:.15f}")
    print(f"  φ⁻¹      = {phi_inv:.15f}")
    print(f"  φ⁻⁷⁰⁹    = {phi_minus_709:.6e}")
    print(f"  φ⁻¹⁰⁰⁰   = {phi_minus_1000:.6e}")
    print()

    daemon = QuadraticDaemon()

    cases = [
        (1.0, -3.0, 2.0),    # D > 0: roots {1, 2}
        (1.0, -2.0, 1.0),    # D = 0: root {1} multiplicity 2
        (1.0,  0.0, 1.0),    # D < 0: roots ±i
        (2.0,  4.0, 2.0),    # D = 0
        (1.0,  1.0, -6.0),   # D > 0: roots {-3, 2}
        (3.0, -2.0, 5.0),    # D < 0
    ]

    for (a, b, c) in cases:
        print(f"─── {a}·x² + {b}·x + {c} = 0 ───")
        resp = daemon.solve(a, b, c)
        print(f"    D           = {resp['discriminant']:.6f}")
        print(f"    kind        = {resp['kind']}")
        for i, r in enumerate(resp["roots"], 1):
            print(f"    x{i}          = {r['real']:.10f}"
                  f" + {r['imag']:+.10f}i")
        print(f"    verify      = {resp['verification']}")
        cel = resp["celestial"]
        print(f"    voice       = {cel['trappist_voice']} "
              f"({cel['voice_freq_hz']:.4f} Hz)")
        print(f"    seal        = {resp['seal'][:32]}…")
        print()
