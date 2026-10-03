#!/usr/bin/env python3
"""Next version of the Eridanus constant scan.

Prints every constant assigned in
canvases/agentic-tilelang-eridanus-dual/eridanus_dual.py
and the integer powers 1..16 that file does not assign.
Unassigned powers are not added to the engine. Nothing here is a seal.
"""
from __future__ import annotations

import math

PHI = (1 + math.sqrt(5)) / 2
SQRT7 = math.sqrt(7)

ASSIGNED = {
    "PHI": PHI,
    "PHI_INV": 1 / PHI,
    "PHI2": PHI ** 2,
    "PHI3": PHI ** 3,
    "PHI4": PHI ** 4,
    "PHI5": PHI ** 5,
    "PHI6": PHI ** 6,
    "PHI7": PHI ** 7,
    "PHI8": PHI ** 8,
    "PHI9": PHI ** 9,
    "PHI10": PHI ** 10,
    "PHI12": PHI ** 12,
    "PHI16": PHI ** 16,
    "PHI26": PHI ** 26,
    "PHI29": PHI ** 29,
    "PHI34": PHI ** 34,
    "PHI92": PHI ** 92,
    "PHI463": PHI ** 463,
    "PHI709": PHI ** (-709),
    "PHI1418": PHI ** (-1418),
    "PHI_MINUS_709": PHI ** (-709),
    "PHI_MINUS_1418": PHI ** (-1418),
    "PHI_NEG_1000": PHI ** (-1000),
    "E": math.e,
    "PI": math.pi,
    "OMEGA_RAD": math.pi / PHI,
    "OMEGA_DEG": math.degrees(math.pi / PHI),
    "SQRT7": SQRT7,
    "KAPPA_EFF": (PHI ** 4) * SQRT7,
}

# Present in the engine. Not missing.
PRESENT_POWERS = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 16, 26, 29, 34, 92, 463}
# 1..16 not assigned. Not referenced by the engine.
ABSENT_1_16 = [n for n in range(1, 17) if n not in PRESENT_POWERS]


def main() -> int:
    for name, value in ASSIGNED.items():
        print(f"{name}\t{value:.16e}")
    print("absent_powers_1_16")
    for n in ABSENT_1_16:
        print(f"PHI{n}\t{PHI ** n:.16e}\tnot_assigned")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
