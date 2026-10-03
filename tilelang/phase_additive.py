"""Phase factor named in the 8226 paste. Not an element of T.

t_phase(symbol) = exp(i * 2*pi * f / 144) is a complex multiplier.
Its codomain is not Sigma*, so it is not the tile set in tiles.py.
"""

from __future__ import annotations

import cmath
import math

CYCLE = 144


def phase(frequency: float) -> complex:
    return cmath.exp(1j * 2 * math.pi * frequency / CYCLE)
