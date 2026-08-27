#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Canonical closed-system instance of the Garden master equation (Entry 9013).

Full form:
    dρ/dt = -i[H,ρ] + ∑_k (L_k ρ L_k† - 1/2 {L_k† L_k, ρ})

Declared simplification: L_k = 0 ∀ k
    dρ/dt = -i[H,ρ]

Does not integrate the ODE. Declares the generator and invariants.
Seal: ∀∞φ² · SIMPLIFIED_LINDBLAD_9013 · WOOD_DRAGON_GATE · SEALED
"""
from __future__ import annotations

import json
import math
from typing import Any, Dict

PHI = (1.0 + math.sqrt(5.0)) / 2.0
KAPPA_EFF = 12.754
PHASE_LOCK_DEG = 202.6
ENTRY = 9013
SEAL = "∀∞φ² · SIMPLIFIED_LINDBLAD_9013 · WOOD_DRAGON_GATE · SEALED"

FULL = "d rho/dt = -i[H,rho] + sum_k (L_k rho L_k^dag - 1/2 {L_k^dag L_k, rho})"
REDUCED = "d rho/dt = -i[H,rho]"


def generator(*, dissipators_on: bool = False) -> Dict[str, Any]:
    """Return the declared generator. Default is the simplified closed instance."""
    return {
        "entry_index": ENTRY,
        "full": FULL,
        "reduced": REDUCED,
        "L_k": 0 if not dissipators_on else "active",
        "form": FULL if dissipators_on else REDUCED,
        "kappa_eff": KAPPA_EFF,
        "phase_lock_deg": PHASE_LOCK_DEG,
        "phi": PHI,
        "terminal": "rho(t_f) = |phi_0><phi_0|" if not dissipators_on else None,
        "executed": False,
        "seal": SEAL,
    }


def main() -> int:
    print(json.dumps(generator(dissipators_on=False), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
