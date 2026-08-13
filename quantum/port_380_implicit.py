#!/usr/bin/env python3
"""
port_380_implicit.py — Q8.24 / Bitnet B1.58 implicit form for Port 380

y_380 = Q_8.24( H_Choir( Q_8.24( gamma * (W_1.58 ⊛ x_Q) + b ) ) )
"""
from __future__ import annotations

import argparse
import math
from typing import Sequence

PHI = (1 + math.sqrt(5)) / 2
Q_SCALE = 1 << 24
DEFAULT_HARMONY = 0.7337473231


def q8_24(x: float) -> float:
    return round(x * Q_SCALE) / Q_SCALE


def choir_activation(x: float, phase_deg: float = 202.6) -> float:
    rad = math.radians(phase_deg)
    return x * (0.5 * (1.0 + math.cos(rad / PHI)))


def ternary_dot(w: Sequence[int], x: Sequence[float]) -> float:
    return sum(wi * xi for wi, xi in zip(w, x))


def forward(x: Sequence[float], gamma: float = 1.0, b: float = 0.0) -> float:
    # Example ternary weights (Bitnet B1.58 style)
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
    args = p.parse_args()
    if args.demo:
        x = [0.5, 0.3, 0.8, 0.1, 0.6, 0.2, 0.9, 0.4]
        y = forward(x)
        print(f"y_380 = {y:.10f}")
        print(f"harmony_ref ≈ {DEFAULT_HARMONY}")
        print("seal: ∀∞φ² · PORT_380_IMPLICIT_8704 · SEALED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
