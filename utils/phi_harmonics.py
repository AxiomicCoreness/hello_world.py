#!/usr/bin/env python3
"""
🜁∀ Phi Harmonics — φ-based utility functions for the sovereign framework
"""

import math
from typing import List

PHI = 1.618033988749895
PHI_INVERSE = 0.6180339887498948


def phi_scale(value: float, steps: int = 1) -> float:
    """Scale a value by φ^n."""
    return value * (PHI ** steps)


def phi_resonance_check(values: List[float], tolerance: float = 0.01) -> bool:
    """Check if a sequence resonates with φ proportions."""
    if len(values) < 2:
        return False
    ratios = [values[i+1] / values[i] for i in range(len(values)-1)]
    return all(abs(r - PHI) < tolerance or abs(r - PHI_INVERSE) < tolerance for r in ratios)
