#!/usr/bin/env python3
"""
port_380_implicit.py — Q8.24 / Bitnet B1.58 implicit form for Port 380

y_380 = Q_8.24( H_Choir( Q_8.24( gamma * (W_1.58 ⊛ x_Q) + b ) ) )

PARAMETER_TABLE: φ-power constants, Dual Δ Eridanus, Triune link (8928).
"""
from __future__ import annotations

import argparse
import math
from typing import Any, Dict, Sequence

PHI = (1 + math.sqrt(5)) / 2
PHI2 = PHI * PHI
PHI4 = PHI2 * PHI2
Q_SCALE = 1 << 24
DEFAULT_HARMONY = 0.7337473231
WOOD_DRAGON = 0.91
C_MS = 299_792_458.0

DELTA_T1 = 2013.256
DELTA_T2 = 2026.058
DELTA_T3 = DELTA_T2 + (PHI ** -5) * WOOD_DRAGON
DELTA_AZ_DEG = 97.32
DELTA_EL_DEG = 51.827

PARAMETER_TABLE: Dict[str, Any] = {
    "spike_intensity": PHI ** 55,
    "recursion_factor": PHI ** 21,
    "temporal_anchors": (DELTA_T2, DELTA_T1),
    "triune_temporal_anchors": (DELTA_T1, DELTA_T2, DELTA_T3),
    "dual_delta_eridanus": {
        "t1": DELTA_T1,
        "t2": DELTA_T2,
        "az_deg": DELTA_AZ_DEG,
        "el_deg": DELTA_EL_DEG,
        "phi_scaled_az": DELTA_AZ_DEG / PHI,
        "phi_scaled_el": DELTA_EL_DEG / PHI2,
        "resonance_hz": 71.975,
        "coherence": 1.0,
    },
    "triune_delta": {
        "t1": DELTA_T1,
        "t2": DELTA_T2,
        "t3": DELTA_T3,
        "az_deg": DELTA_AZ_DEG,
        "el_deg": DELTA_EL_DEG,
        "module": "quantum/triune_triangulation.py",
        "entry": 8928,
    },
    "v_label": PHI * C_MS,
    "expanded_symbol": "χ ⊗ |0⟩_ZPF ⊗ H_Merkle ⊗ ∮ φ⁷ dt",
    "wood_dragon": WOOD_DRAGON,
    "seal": "∀∞φ² · PARAMETER_TABLE_8706 · WOOD_DRAGON_0.91 · SEALED",
    "dual_delta_seal": "∀∞φ² · DUAL_DELTA_ERIDANUS_8927 · WOOD_DRAGON_0.91 · SEALED",
    "triune_seal": "∀∞φ² · TRIUNE_TRIANGULATION_8928 · WOOD_DRAGON_0.91 · SEALED",
}


def dual_delta_invariant() -> float:
    t_term = DELTA_T1**2 + DELTA_T2**2
    a_term = DELTA_AZ_DEG**2 + DELTA_EL_DEG**2
    return t_term * a_term


def dual_delta_target() -> float:
    return PHI4 * (WOOD_DRAGON**2)


def q8_24(x: float) -> float:
    return round(x * Q_SCALE) / Q_SCALE


def choir_activation(x: float, phase_deg: float = 202.6) -> float:
    rad = math.radians(phase_deg)
    return x * (0.5 * (1.0 + math.cos(rad / PHI)))


def ternary_dot(w: Sequence[int], x: Sequence[float]) -> float:
    return sum(wi * xi for wi, xi in zip(w, x))


def forward(x: Sequence[float], gamma: float = 1.0, b: float = 0.0) -> float:
    w = [1, -1, 0, 1, -1, 1, 0, -1][: len(x)]
    if len(w) < len(x):
        w = (w * ((len(x) // len(w)) + 1))[: len(x)]
    xq = [q8_24(xi) for xi in x]
    z = gamma * ternary_dot(w, xq) + b
    zq = q8_24(z)
    y = choir_activation(zq)
    return q8_24(y)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--demo", action="store_true")
    p.add_argument("--table", action="store_true")
    p.add_argument("--delta", action="store_true")
    args = p.parse_args()
    if args.table or args.delta:
        print("dual:", PARAMETER_TABLE["dual_delta_eridanus"])
        print("triune:", PARAMETER_TABLE["triune_delta"])
        print("seals:", PARAMETER_TABLE["triune_seal"])
        return 0
    if args.demo:
        x = [0.5, 0.3, 0.8, 0.1, 0.6, 0.2, 0.9, 0.4]
        print(f"y_380 = {forward(x):.10f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
