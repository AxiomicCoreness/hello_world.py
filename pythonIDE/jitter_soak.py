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
"""
pythonIDE/jitter_soak.py — jitter correction + soak, merged with prior stack.

Prior tasks this module sits beside (does not rewrite):
  scripts/self_seal.py              — signitorial (Integrity/Seal/Witness/Combined)
  pythonIDE/dephasing.py            — Lindblad dephasing γ_k = φ^{-(k+1)}
  pythonIDE/lindblad_port_hamiltonian.py — conditional port-Hamiltonian bridge
  pythonIDE/dX_dt.py                — system ODE + integrate() soak horizon

This module adds a *classical pulse-envelope* damping term:
  γ_jitter = φ⁻⁸ ≈ 0.021286
for high-frequency jitter suppression over a 10 s soak. That γ is not the
dephasing ladder and is not claimed to be a measured Lindblad spectral gap.

Attribution: Clarke Yoursa Tee sits in LICENSE / CITATION.cff / README /
notice.md / PROVENANCE.md headers (signitorial name-in-masked-body target).

No ledger write. MCP unfilled. No 0.0.0.0 bind.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Tuple

PHI = (1.0 + math.sqrt(5.0)) / 2.0
PHI2 = PHI * PHI  # starfire harmonic label
PHI3 = PHI2 * PHI

# Jitter / soak constants (from merge paste; φ-scaled)
GAMMA_JITTER = PHI ** (-8)  # ≈ 0.021286 — envelope damping, not dephasing γ_k
DELTA_THETA_AMP = 0.018  # φ-harmonic modulation amplitude
TAU_PULSE_MS = 23.61  # pulse decay envelope (ms)
T_MAX_SOAK_DEFAULT = 10.0  # seconds

NINJA_NUMBERS = [144, 233, 377, 610, 987, 1597, 2584]
NINJA_ROLES = [
    "OBSERVATION",
    "RESONANCE",
    "HARMONIZATION",
    "SYNTHESIS",
    "INTEGRATION",
    "PERPETUATION",
    "TRANSCENDENCE",
]


@dataclass
class JitterSoakState:
    """Mutable soak parameters after apply_jitter_correction."""

    t_max_soak: float = T_MAX_SOAK_DEFAULT
    gamma: float = GAMMA_JITTER
    delta_theta_amp: float = DELTA_THETA_AMP
    tau_pulse_ms: float = TAU_PULSE_MS
    starfire_freq: float = PHI2
    activated: bool = False


def apply_jitter_correction(state: JitterSoakState | None = None) -> JitterSoakState:
    """Activate jitter correction and extend integration soak to 10 s.

    Prints the operational summary from the merge paste. Returns the
    updated state (creates one if None).
    """
    st = state or JitterSoakState()
    st.t_max_soak = T_MAX_SOAK_DEFAULT
    st.gamma = GAMMA_JITTER
    st.delta_theta_amp = DELTA_THETA_AMP
    st.tau_pulse_ms = TAU_PULSE_MS
    st.starfire_freq = PHI2
    st.activated = True

    print("\n🌀 JITTER CORRECTION & SOAK ACTIVATED")
    print("   • Integration soak extended to 10 seconds")
    print("   • Lindblad-like damping term added to suppress high-frequency jitter")
    print(f"   • Effective damping coefficient: γ = φ⁻⁸ ≈ {st.gamma:.6f}")
    print(f"   • δθ amplitude remains {st.delta_theta_amp} (φ-harmonic modulation)")
    print(f"   • Decay envelope τ_pulse = {st.tau_pulse_ms} ms")
    print("   • Soak test will run for 10 seconds – press Ctrl+C to interrupt.\n")
    return st


def pulse_envelope(t_ms: float, tau_ms: float = TAU_PULSE_MS) -> float:
    """exp(-t/τ) pulse envelope; t and τ in milliseconds."""
    if tau_ms <= 0:
        raise ValueError("tau_ms must be positive")
    return math.exp(-max(t_ms, 0.0) / tau_ms)


def damped_theta(
    t_s: float,
    amp: float = DELTA_THETA_AMP,
    gamma: float = GAMMA_JITTER,
    omega: float = PHI2,
) -> float:
    """δθ(t) = amp · exp(-γ t) · sin(ω t) — classical jitter-suppressed oscillation."""
    return amp * math.exp(-gamma * t_s) * math.sin(omega * t_s)


def soak_trace(
    t_max: float = T_MAX_SOAK_DEFAULT,
    dt: float = 0.01,
    amp: float = DELTA_THETA_AMP,
    gamma: float = GAMMA_JITTER,
) -> List[Tuple[float, float]]:
    """Sample (t, δθ(t)) over the soak horizon."""
    if dt <= 0:
        raise ValueError("dt must be positive")
    out: List[Tuple[float, float]] = []
    t = 0.0
    while t <= t_max + 1e-15:
        out.append((t, damped_theta(t, amp=amp, gamma=gamma)))
        t += dt
    return out


def ninja_table() -> List[Tuple[int, str]]:
    """Pair Fibonacci-adjacent ninja numbers with roles (length-matched)."""
    n = min(len(NINJA_NUMBERS), len(NINJA_ROLES))
    return list(zip(NINJA_NUMBERS[:n], NINJA_ROLES[:n]))


def _smoke() -> None:
    st = apply_jitter_correction()
    assert st.activated
    assert abs(st.t_max_soak - 10.0) < 1e-12
    assert abs(st.gamma - PHI ** (-8)) < 1e-12
    assert abs(pulse_envelope(0.0) - 1.0) < 1e-12
    assert pulse_envelope(TAU_PULSE_MS) < math.exp(-0.99)
    tr = soak_trace(t_max=0.5, dt=0.1)
    assert len(tr) >= 5
    # damping: late amplitude envelope smaller than early peak bound
    early = max(abs(y) for _, y in tr[:3])
    late = max(abs(y) for _, y in tr[-3:])
    assert late <= early + 1e-9 or early < 1e-6
    pairs = ninja_table()
    assert len(pairs) == 7
    assert pairs[0] == (144, "OBSERVATION")
    assert pairs[-1] == (2584, "TRANSCENDENCE")
    print("jitter_soak smoke: PASS")
    print(f"  γ_jitter = φ⁻⁸ ≈ {GAMMA_JITTER:.6f}")
    print(f"  starfire_freq = φ² ≈ {PHI2:.6f}")
    print(f"  ninja roles: {len(pairs)}")
    print("  link: dephasing.py (γ_k ladder) · lindblad_port_hamiltonian.py (J-R)")
    print("  link: dX_dt.integrate soak · scripts/self_seal.py signitorial")


if __name__ == "__main__":
    _smoke()
