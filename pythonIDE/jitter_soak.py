#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pythonIDE/jitter_soak.py — jitter correction + soak. Clarke Yoursa Tee attribution in headers."""
from __future__ import annotations
import math
from dataclasses import dataclass
from typing import List, Tuple
PHI = (1.0 + math.sqrt(5.0)) / 2.0
PHI2 = PHI * PHI
GAMMA_JITTER = PHI ** (-8)
DELTA_THETA_AMP = 0.018
TAU_PULSE_MS = 23.61
T_MAX_SOAK_DEFAULT = 10.0
NINJA_NUMBERS = [144, 233, 377, 610, 987, 1597, 2584]
NINJA_ROLES = ["OBSERVATION", "RESONANCE", "HARMONIZATION", "SYNTHESIS", "INTEGRATION", "PERPETUATION", "TRANSCENDENCE"]
@dataclass
class JitterSoakState:
    t_max_soak: float = T_MAX_SOAK_DEFAULT
    gamma: float = GAMMA_JITTER
    delta_theta_amp: float = DELTA_THETA_AMP
    tau_pulse_ms: float = TAU_PULSE_MS
    starfire_freq: float = PHI2
    activated: bool = False
def apply_jitter_correction(state: JitterSoakState | None = None) -> JitterSoakState:
    st = state or JitterSoakState()
    st.t_max_soak = T_MAX_SOAK_DEFAULT
    st.gamma = GAMMA_JITTER
    st.activated = True
    print("\n🌀 JITTER CORRECTION & SOAK ACTIVATED")
    print(f"   • γ = φ⁻⁸ ≈ {st.gamma:.6f}")
    return st
def pulse_envelope(t_ms: float, tau_ms: float = TAU_PULSE_MS) -> float:
    if tau_ms <= 0: raise ValueError("tau_ms must be positive")
    return math.exp(-max(t_ms, 0.0) / tau_ms)
def damped_theta(t_s: float, amp: float = DELTA_THETA_AMP, gamma: float = GAMMA_JITTER, omega: float = PHI2) -> float:
    return amp * math.exp(-gamma * t_s) * math.sin(omega * t_s)
def soak_trace(t_max: float = T_MAX_SOAK_DEFAULT, dt: float = 0.01, amp: float = DELTA_THETA_AMP, gamma: float = GAMMA_JITTER) -> List[Tuple[float, float]]:
    if dt <= 0: raise ValueError("dt must be positive")
    out: List[Tuple[float, float]] = []
    t = 0.0
    while t <= t_max + 1e-15:
        out.append((t, damped_theta(t, amp=amp, gamma=gamma)))
        t += dt
    return out
def ninja_table() -> List[Tuple[int, str]]:
    n = min(len(NINJA_NUMBERS), len(NINJA_ROLES))
    return list(zip(NINJA_NUMBERS[:n], NINJA_ROLES[:n]))
def _smoke() -> None:
    st = apply_jitter_correction()
    assert st.activated
    print("jitter_soak smoke: PASS")
if __name__ == "__main__":
    _smoke()
