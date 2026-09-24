#!/usr/bin/env python3
"""celestial/phi_constants.py — single source of φ powers.

Signitorial: Clarke Yoursa Tee
Seal:        ∀∞φ² · PHI_CONSTANTS · WOOD_DRAGON_0.91 · SEALED
MCP:         unfilled
Dual ASGI:   127.0.0.1:8024

Values are computed, not pasted. D19: PHI_MINUS_1000 is φ⁻¹⁰⁰⁰
(≈1.028868e-209), not the φ⁻¹⁴¹⁸ literal 4.524e-297.

No I/O on import. No BASE_DIR mkdir. Optional deps are flags only.
Import this module; do not copy the header into every file.
"""
from __future__ import annotations

import math
from typing import Any

# ── optional deps (flags; unused imports stay None) ───────────────────
try:
    import numpy as np  # noqa: F401
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    np = None  # type: ignore[assignment]

try:
    from scipy.integrate import solve_ivp  # noqa: F401
    from scipy.special import zeta as scipy_zeta  # noqa: F401
    from scipy.special import gamma as gamma_func
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False
    solve_ivp = None  # type: ignore[assignment]
    scipy_zeta = None  # type: ignore[assignment]
    gamma_func = math.gamma

try:
    import yaml  # noqa: F401
    HAS_YAML = True
except ImportError:
    HAS_YAML = False
    yaml = None  # type: ignore[assignment]

try:
    import matplotlib.pyplot as plt  # noqa: F401
    HAS_MPL = True
except ImportError:
    HAS_MPL = False
    plt = None  # type: ignore[assignment]

try:
    import requests  # noqa: F401
except ImportError:
    requests = None  # type: ignore[assignment]
HAS_REQUESTS = requests is not None

# ── φ ladder (computed) ───────────────────────────────────────────────
phi = (1.0 + math.sqrt(5.0)) / 2.0
phi2 = phi ** 2
phi3 = phi ** 3
phi4 = phi ** 4
phi5 = phi ** 5
phi6 = phi ** 6
phi7 = phi ** 7
phi8 = phi ** 8
phi9 = phi ** 9
phi12 = phi ** 12
phi13 = phi ** 13
phi14 = phi ** 14
phi21 = phi ** 21
phi34 = phi ** 34
phi709 = phi ** 709
phi713 = phi ** 713
phi_minus_709 = phi ** (-709)
phi_minus_1000 = phi ** (-1000)
phi_minus_1418 = phi ** (-1418)
phi_inv = 1.0 / phi

PHI = phi
PHI2 = phi2
PHI3 = phi3
PHI4 = phi4
PHI5 = phi5
PHI6 = phi6
PHI7 = phi7
PHI8 = phi8
PHI9 = phi9
PHI12 = phi12
PHI13 = phi13
PHI14 = phi14
PHI21 = phi21
PHI34 = phi34
PHI709 = phi709
PHI713 = phi713
PHI_MINUS_709 = phi_minus_709
PHI_MINUS_1000 = phi_minus_1000
PHI_MINUS_1418 = phi_minus_1418
PHI_NEG_1418 = phi_minus_1418
PHI_INV = phi_inv

# Asserted (not derived) anchors — D11 / D16 remain OPEN.
NORTH_STAR_FREQ = 71.975
NORTH_STAR_HZ = NORTH_STAR_FREQ
PSI4_CARRIER_HZ = 162.28e12  # D16: 162.28 THz asserted, no preimage
CHIRON_PHASE_LOCK = 202.6

# Quota floors that actually are floors (D21).
FLOOR_PHI2 = int(math.floor(phi2))   # 2
FLOOR_PHI4 = int(math.floor(phi4))   # 6
FLOOR_PHI5 = int(math.floor(phi5))   # 11
FLOOR_PHI6 = int(math.floor(phi6))   # 17  — paste used 18 and pods=13
FLOOR_PHI8 = int(math.floor(phi8))   # 46  — paste used services=8 (F₆)


def env_literals() -> dict[str, str]:
    """String forms for k8s env — computed, not hand-typed."""
    return {
        "PHI": f"{PHI:.15f}",
        "PHI2": f"{PHI2:.15f}",
        "PHI3": f"{PHI3:.15f}",
        "PHI4": f"{PHI4:.15f}",
        "PHI5": f"{PHI5:.15f}",
        "PHI6": f"{PHI6:.15f}",
        "PHI7": f"{PHI7:.15f}",
        "PHI8": f"{PHI8:.15f}",
        "PHI_INV": f"{PHI_INV:.15f}",
        "PHI_MINUS_709": f"{PHI_MINUS_709:.15e}",
        "PHI_MINUS_1000": f"{PHI_MINUS_1000:.15e}",
        "PHI_MINUS_1418": f"{PHI_MINUS_1418:.15e}",
    }


def capability_flags() -> dict[str, Any]:
    return {
        "has_numpy": HAS_NUMPY,
        "has_scipy": HAS_SCIPY,
        "has_yaml": HAS_YAML,
        "has_mpl": HAS_MPL,
        "has_requests": HAS_REQUESTS,
    }


def _selfcheck() -> None:
    """D19: the 4.524e-297 literal is φ⁻¹⁴¹⁸, not φ⁻¹⁰⁰⁰."""
    ghost = 4.524036764254231e-297
    rel_1418 = abs(PHI_MINUS_1418 - ghost) / abs(ghost)
    rel_1000 = abs(PHI_MINUS_1000 - ghost) / abs(PHI_MINUS_1000)
    assert rel_1418 < 1e-12, f"φ⁻¹⁴¹⁸ drifted from known literal: {rel_1418}"
    assert rel_1000 > 0.5, "PHI_MINUS_1000 must not equal the φ⁻¹⁴¹⁸ ghost"
    assert FLOOR_PHI6 == 17
    assert FLOOR_PHI8 == 46


_selfcheck()


if __name__ == "__main__":
    print("🜁∀ celestial.phi_constants selfcheck")
    print(f"  PHI            = {PHI:.15f}")
    print(f"  PHI_MINUS_1000 = {PHI_MINUS_1000:.15e}  (φ⁻¹⁰⁰⁰)")
    print(f"  PHI_MINUS_1418 = {PHI_MINUS_1418:.15e}  (φ⁻¹⁴¹⁸)")
    print(f"  FLOOR_PHI6     = {FLOOR_PHI6}  FLOOR_PHI8 = {FLOOR_PHI8}")
    print(f"  flags          = {capability_flags()}")
    print("  D19 selfcheck PASS")
