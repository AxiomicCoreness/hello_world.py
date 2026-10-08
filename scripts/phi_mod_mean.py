#!/usr/bin/env python3
"""Hard assert for the stated golden-mod mean. No ledger write.

N = 510510. Target mean 255255 is N/2, not a derived result.
Missing engine file exits 1. A wrong mean exits 1.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

PHI = (1.0 + math.sqrt(5.0)) / 2.0
N = 510510
TARGET = 255255.0
TOLERANCE_REL = 1e-6
ENGINE = Path(__file__).resolve().parent / "clarke_engine.py"


def mean() -> float:
    total = sum((i * PHI) % N for i in range(1, N + 1))
    return total / N


def main() -> int:
    if not ENGINE.is_file():
        print("engine absent", file=sys.stderr)
        return 1
    value = mean()
    rel = abs(value - TARGET) / TARGET
    print(f"mean={value:.6f} target={TARGET:.1f} rel={rel:.6e}")
    return 0 if rel <= TOLERANCE_REL else 1


if __name__ == "__main__":
    raise SystemExit(main())
