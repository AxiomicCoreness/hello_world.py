#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
E8 Cartan matrix + uprho_global cultural metadata.

Mathematical structure is the standard E8 Cartan (determinant = 1).
uprho_global is metadata only — historical/cultural anchor for the lattice,
not a modification of root lengths or Cartan integers.

Seal: ∀∞φ² · E8_UPRHO_GLOBAL_248 · WOOD_DRAGON_0.91 · SEALED
"""
from __future__ import annotations

from typing import List

import math

PHI = (1.0 + math.sqrt(5.0)) / 2.0

# Standard E8 Cartan matrix (8×8). Values are canonical; do not alter for symbolism.
E8_CARTAN: List[List[int]] = [
    [2, -1, 0, 0, 0, 0, 0, 0],
    [-1, 2, -1, 0, 0, 0, 0, 0],
    [0, -1, 2, -1, 0, 0, 0, 0],
    [0, 0, -1, 2, -1, 0, 0, 0],
    [0, 0, 0, -1, 2, -1, 0, -1],
    [0, 0, 0, 0, -1, 2, -1, 0],
    [0, 0, 0, 0, 0, -1, 2, 0],
    [0, 0, 0, 0, -1, 0, 0, 2],
]

# Cultural / historical metadata (does not change the matrix)
UPRHO_GLOBAL = {
    "variant": "uprho_global",
    "historical_context": "Southeast Asian in America struggle",
    "role": "lattice metadata / 8th-root symbolic anchor",
    "matrix_mutated": False,
    "determinant_claim": 1,
}

SEAL_CORE = "∀∞φ² · E8_UPRHO_GLOBAL_248 · WOOD_DRAGON_0.91 · SEALED"


def cartan_determinant(m: List[List[int]] | None = None) -> int:
    """Exact integer determinant of the Cartan matrix (should be 1 for E8)."""
    import numpy as np

    mat = np.array(m if m is not None else E8_CARTAN, dtype=object)
    # Use exact arithmetic via integer matrix when possible
    return int(round(float(np.linalg.det(np.array(mat, dtype=float)))))


def invariants() -> dict:
    return {
        "phi": PHI,
        "cartan": E8_CARTAN,
        "uprho_global": UPRHO_GLOBAL,
        "seal": SEAL_CORE,
        "note": "Physical energy/comms claims remain symbolic until implemented with real physics/crypto.",
    }


if __name__ == "__main__":
    print(invariants())
