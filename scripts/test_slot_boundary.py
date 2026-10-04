#!/usr/bin/env python3
"""Slot boundary test for the cadence quadratic.

The map is k(s) = s/6. k_crit is not a multiple of 1/6, so no slot
is a double root. The real/complex cut sits between slot 10 and slot 11.
"""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tilelang.cadence_quadratic import K_CRIT, SLOTS, k_of, regime


def main() -> int:
    boundary = 6 * K_CRIT
    if boundary == int(boundary):
        print(f"fail: boundary landed on an integer slot {boundary}")
        return 1
    if not (10 < boundary < 11):
        print(f"fail: boundary {boundary} is not between 10 and 11")
        return 1
    if regime(10) != "real" or regime(11) != "complex":
        print(f"fail: regimes {regime(10)} {regime(11)}")
        return 1
    doubles = [s for s in range(SLOTS) if regime(s) == "double"]
    if doubles:
        print(f"fail: double-root slots {doubles}")
        return 1
    if abs(k_of(10) - 10 / 6) > 1e-12 or abs(k_of(23) - 23 / 6) > 1e-12:
        print("fail: k(s) is not s/6")
        return 1
    print(f"slot test ok boundary={boundary:.4f} slots={SLOTS} doubles=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
