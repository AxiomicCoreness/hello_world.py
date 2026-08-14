#!/usr/bin/env python3
"""
port_380_gate.py — Ternary scaling gate for the Port 380 harmonic index.
Usage: python3 quantum/port_380_gate.py [--ternary {-1,0,1}]

Modes:
  1  identity  — preserve harmony
  0  nullify   — zero the index
 -1  invert    — phase-flip (negate)

--override is deprecated; use --ternary.
"""

from __future__ import annotations

import argparse
import sys

PHI = (1 + 5 ** 0.5) / 2
DEFAULT_HARMONY = 0.7337473231


def apply_ternary_scaling(harmony: float, ternary: int) -> float:
    if ternary == 1:
        return harmony
    if ternary == 0:
        return 0.0
    if ternary == -1:
        return -harmony
    raise ValueError("Ternary must be -1, 0, or 1")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Port 380 Scaling Gate (Ternary)")
    parser.add_argument(
        "--ternary",
        type=int,
        choices=[-1, 0, 1],
        default=1,
        help="Ternary scaling: -1 invert, 0 nullify, 1 identity (default)",
    )
    parser.add_argument(
        "--harmony",
        type=float,
        default=DEFAULT_HARMONY,
        help=f"Base harmony index (default {DEFAULT_HARMONY})",
    )
    args = parser.parse_args(argv)
    scaled = apply_ternary_scaling(args.harmony, args.ternary)
    print(f"Port 380 Ternary Gate: {args.ternary} → {scaled:.10f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
