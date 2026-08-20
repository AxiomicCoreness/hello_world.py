"""PHI / phase-lock constants for production layout.

Does not rewrite existing modules; centralizes names used across the Garden.
"""
from __future__ import annotations

import math

PHI: float = (1.0 + math.sqrt(5.0)) / 2.0
PHI2: float = PHI * PHI
PHASE_LOCK_DEG: float = 202.6
WEYL_ORDER_E8: int = 696_729_600
OPERATOR: str = "ClarkeYoursaTee"
