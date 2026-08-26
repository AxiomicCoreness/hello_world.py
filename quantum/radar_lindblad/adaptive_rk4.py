#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
quantum/radar_lindblad/adaptive_rk4.py — Entry 8762

Adaptive RK4 time-step for Lindblad / ladder integrations:
    dt = 1/(2·f_max)·φ⁻¹

Re-exports hybrid_rk4_simulator adaptive API for the radar_lindblad quadrant.
Physics invariants (unitarity, hermiticity, positivity, entropy floor) unchanged.
"""
from __future__ import annotations

from hybrid_rk4_simulator import (  # noqa: F401
    F_144,
    PHI_INV,
    adaptive_dt,
    adaptive_rk4_step,
    rk4_step_float,
    verify_rk4_convergence,
)

__all__ = [
    "F_144",
    "PHI_INV",
    "adaptive_dt",
    "adaptive_rk4_step",
    "rk4_step_float",
    "verify_rk4_convergence",
]

if __name__ == "__main__":
    r = verify_rk4_convergence()
    print(r)
