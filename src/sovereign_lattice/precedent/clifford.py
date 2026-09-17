"""Clifford chain — invariant seed for all sovereign transforms."""

from dataclasses import dataclass
import math

PHI = (1 + math.sqrt(5)) / 2
PHI3 = PHI ** 3
CLIFFORD_SIGNATURE = (3, 1)  # Cl(3,1)

@dataclass
class CliffordSeed:
    phi: float = PHI
    tau: float = 0.5983          # seconds
    normalization: float = 1 / math.sqrt(4 * math.pi)
    signature: tuple = CLIFFORD_SIGNATURE
    origin: tuple = (0, 0)

CLIFFORD_SEED = CliffordSeed()
