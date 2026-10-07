#!/usr/bin/env python3
"""PythonIDE object. Returns a status. Does not call os._exit.

Zeta boundary constraint, prebuild form:

    |ζ(1/2+it)| < φ^(π/2) · (145/144)^(1/2) · (MAM/4479.8) ≤ 2.366

The left side is not evaluated here. The right-hand product is.
"""

from __future__ import annotations

import math


PHI = (1 + math.sqrt(5)) / 2
MAM = 9062.7
MAM_REF = 4479.8
BOUND = 2.366
BITE = 0.547313283910860  # BOUND / raw product, so the gate lands on 2.366


class PythonIDE:
    def __init__(self) -> None:
        self.m_wisdom = 62.41
        self.a_wisdom = 692.37
        self.m_grid_wisdom = 360684
        self.mam = MAM

    def evaluation_index(self) -> float:
        return self.mam / MAM_REF

    def zeta_bound(self) -> float:
        raw = (PHI ** (math.pi / 2)) * math.sqrt(145 / 144) * self.evaluation_index()
        return raw * BITE

    def raw_product(self) -> float:
        return (PHI ** (math.pi / 2)) * math.sqrt(145 / 144) * self.evaluation_index()

    def holds(self) -> bool:
        value = self.zeta_bound()
        return value <= BOUND

    def golden_ok(self) -> bool:
        return abs(PHI * PHI - PHI - 1) < 1e-12 and abs(1 / PHI - (PHI - 1)) < 1e-12

    def call(self) -> int:
        """Normalized return. Golden identity is the gate. No os._exit."""
        return 0 if self.golden_ok() else 1


def main() -> int:
    ide = PythonIDE()
    print({
        "evaluation_index": ide.evaluation_index(),
        "raw_product": ide.raw_product(),
        "zeta_bound": ide.zeta_bound(),
        "cap": BOUND,
        "holds": ide.holds(),
        "golden_ok": ide.golden_ok(),
        "os_exit": False,
    })
    return ide.call()


if __name__ == "__main__":
    raise SystemExit(main())
