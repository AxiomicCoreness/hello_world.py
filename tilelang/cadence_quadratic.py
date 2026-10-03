#!/usr/bin/env python3
"""Cadence to the locked quadratic. Slot index is the only input.

24 slots, 15 minutes each, one 6-hour window.
k(s) = s / 6, so s = 24 would be the classical k = 4.
Real part does not depend on s.
"""

import math

A = ((1 + math.sqrt(5)) / 2) * 0.934 ** 2
B = math.pi * 0.910 ** 2
C = math.e
K_CRIT = (B * B) / (A * C)
RE = -B / (2 * A)
SLOTS = 24


def k_of(slot: int) -> float:
    if not 0 <= slot < SLOTS:
        raise ValueError("slot must be in 0..23")
    return slot / 6.0


def regime(slot: int) -> str:
    k = k_of(slot)
    delta = B * B - k * A * C
    if abs(delta) < 1e-12:
        return "double"
    return "real" if delta > 0 else "complex"


def main() -> int:
    print(f"k_crit={K_CRIT:.6f}  Re={RE:.6f}")
    for s in range(SLOTS):
        print(f"s={s:02d}  k={k_of(s):.3f}  {regime(s)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
