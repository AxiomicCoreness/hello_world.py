#!/usr/bin/env python3
"""Eridanus flow. A step equation, not a date.

The parameter n is a chain-position label. It is not wall-clock time
and it is not the legend token. This module does not import
legend_anchor and does not convert any token to a datetime.

Family: Φ(x). One step of

    dΦ/dτ = φ⁻¹ (1 − Φ)

on a scalar state. τ is the step count.
"""

from __future__ import annotations

import math

PHI = (1 + math.sqrt(5)) / 2
PHI_INV = 1 / PHI


def step(phi_state: float, dtau: float = 0.01) -> float:
    if dtau <= 0:
        raise ValueError("dtau must be positive")
    return phi_state + dtau * PHI_INV * (1.0 - phi_state)


def run(n: int, phi_state: float = 0.0, steps: int = 1, dtau: float = 0.01) -> dict:
    """n is a position label. It does not enter the derivative."""
    if n < 0:
        raise ValueError("position label must be non-negative")
    state = phi_state
    for _ in range(steps):
        state = step(state, dtau)
    return {
        "family": "eridanus_flow",
        "position_label": n,
        "phi_state": state,
        "steps": steps,
        "fixed_point": 1.0,
        "uses_legend_token_as_date": False,
    }


def main() -> int:
    print(run(9268, phi_state=0.0, steps=10))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
