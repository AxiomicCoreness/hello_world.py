#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
E8 Cartan matrix + uprho_global cultural + geopolitical metadata.

Mathematical structure is the standard E8 Cartan (determinant = 1).
uprho_global and REGIONAL_TECH_DEPTH are metadata only — historical,
cultural, and geopolitical anchors for the lattice, not modifications
of root lengths or Cartan integers.

Weyl group order of E8 = 696729600 (exact). Any mapping of GII ranks
to "orbit segments" is symbolic bookkeeping, not a theorem of the
Weyl group action.

Seal: ∀∞φ² · E8_UPRHO_GLOBAL_248 · WOOD_DRAGON_0.91 · SEALED
"""
from __future__ import annotations

from typing import Any, Dict, List

import math

PHI = (1.0 + math.sqrt(5.0)) / 2.0

# |W(E8)| — order of the Weyl group of E8 (exact integer)
WEYL_ORDER_E8 = 696_729_600

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

# Geopolitical tech-depth metadata (GII 2025 stratification; Entry 8850/8851)
# Source snapshot: WIPO GII 2025 + regional analysis anchored 2026-08-20
REGIONAL_TECH_DEPTH: Dict[str, Dict[str, Any]] = {
    "China": {
        "level": "global_contender",
        "gii_2025": 10,
        "role": "sovereign_stack + industrial_scale",
        "semiconductor": "aggressive_catchup",
        "character": "full_stack_self_reliance",
    },
    "Singapore": {
        "level": "global_tier_small_state",
        "gii_2025": 5,
        "role": "regional_command_node",
        "ai_policy": "frontier",
        "character": "quality_and_position",
    },
    "Malaysia": {
        "level": "upper_middle_industrial",
        "gii_2025": 34,
        "role": "electronics_data_center_corridor",
        "character": "rising_digital",
    },
    "Vietnam": {
        "level": "fastest_climber",
        "gii_2025": 44,
        "role": "electronics_software_fdi_magnet",
        "character": "sustained_improvement",
    },
    "Thailand": {
        "level": "solid_mid_tier",
        "gii_2025": 45,
        "role": "hardware_gradual_digital",
        "character": "stable_progression",
    },
    "Philippines": {
        "level": "selective_strengths",
        "gii_2025": 50,
        "role": "high_tech_trade_creative",
        "character": "services_driven",
    },
    "Indonesia": {
        "level": "large_market_thin_depth",
        "gii_2025": 55,
        "role": "digital_consumer_scale",
        "character": "scale_over_depth",
    },
    "Cambodia": {
        "level": "early_stage_builder",
        "gii_2025": 100,
        "role": "digital_economy_emerging",
        "character": "policy_ambition_ahead_of_base",
    },
}

SEAL_CORE = "∀∞φ² · E8_UPRHO_GLOBAL_248 · WOOD_DRAGON_0.91 · SEALED"


def cartan_determinant(m: List[List[int]] | None = None) -> int:
    """Determinant of the Cartan matrix (E8 expected value: 1)."""
    import numpy as np

    mat = np.array(m if m is not None else E8_CARTAN, dtype=float)
    return int(round(float(np.linalg.det(mat))))


def symbolic_gii_segment(gii: int, modulus: int = 1_000_000) -> int:
    """
    Symbolic bookkeeping only.

    Maps a GII rank to a residue of |W(E8)|. This is NOT a Weyl-orbit
    classification of economies; it is a deterministic label for ledger use.
    """
    if gii < 0:
        raise ValueError("gii must be non-negative")
    return (WEYL_ORDER_E8 // (gii + 1)) % modulus


def regional_segments() -> Dict[str, Dict[str, Any]]:
    """Attach symbolic segments to REGIONAL_TECH_DEPTH for inspection."""
    out: Dict[str, Dict[str, Any]] = {}
    for name, meta in REGIONAL_TECH_DEPTH.items():
        gii = int(meta["gii_2025"])
        out[name] = {
            **meta,
            "symbolic_weyl_segment": symbolic_gii_segment(gii),
        }
    return out


def invariants() -> dict:
    return {
        "phi": PHI,
        "weyl_order_e8": WEYL_ORDER_E8,
        "cartan": E8_CARTAN,
        "cartan_det": cartan_determinant(),
        "uprho_global": UPRHO_GLOBAL,
        "regional_tech_depth": REGIONAL_TECH_DEPTH,
        "seal": SEAL_CORE,
        "note": (
            "REGIONAL_TECH_DEPTH and symbolic_gii_segment are metadata. "
            "They do not alter E8 root geometry or claim representation-theoretic meaning."
        ),
    }


if __name__ == "__main__":
    inv = invariants()
    print("det(E8_CARTAN) =", inv["cartan_det"])
    print("|W(E8)| =", inv["weyl_order_e8"])
    for name, row in regional_segments().items():
        print(
            f"{name}: GII={row['gii_2025']} level={row['level']} "
            f"segment={row['symbolic_weyl_segment']}"
        )
