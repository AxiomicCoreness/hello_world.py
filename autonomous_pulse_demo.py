#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
autonomous_pulse_demo.py — Master-equation demonstration of autonomous automation.

Maps the Garden's push/cron/restart loop onto:
  dX/dt = -Λ·(X - X_target) + H(η) + Z(ζ) + R(A_trunc, ρ) + P_PID(e)

Entry 0042 · ∀∞φ² · AUTONOMOUS_MASTER_EQ_0042 · WOOD_DRAGON_GATE · SEALED
"""
from __future__ import annotations

import hashlib
import hmac
import json
import math
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

PHI = (1.0 + math.sqrt(5.0)) / 2.0
PHI_INV = 1.0 / PHI
PHI2 = PHI * PHI
GAMMA = 1.0 / math.sqrt(5.0)
TAU_FRB = 78624.0          # s (~0.91 d)
CRON_DT = 6.0 * 3600.0     # 21600 s — scheduled pulse interval
KP, KI, KD = PHI2, PHI_INV, PHI ** (-2)
PSD = 5.774


def coherence_step(C: float, dt: float) -> float:
    """Analytic step of dC/dt = -γ(C-1)."""
    return 1.0 - (1.0 - C) * math.exp(-GAMMA * dt)


def phase_advance(t: float, dt: float) -> float:
    """φ_p(t) = 2π t / τ_FRB (mod 2π)."""
    return (2.0 * math.pi * (t + dt) / TAU_FRB) % (2.0 * math.pi)


@dataclass
class PhiPID:
    integral: float = 0.0
    prev_error: float = 0.0

    def update(self, setpoint: float, measurement: float, dt: float) -> float:
        e = setpoint - measurement
        self.integral += e * dt
        d = (e - self.prev_error) / dt if dt > 0 else 0.0
        self.prev_error = e
        return KP * e + KI * self.integral + KD * d


@dataclass
class AutonomousState:
    """Discrete state sampled by automation."""
    t: float = 0.0
    C: float = 0.9
    phi_p: float = 0.0
    W: float = 0.1
    rho: float = PSD
    E: float = 0.0
    seals: List[str] = field(default_factory=list)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "t": self.t,
            "C": self.C,
            "phi_p": self.phi_p,
            "phi_deg": math.degrees(self.phi_p),
            "W": self.W,
            "rho": self.rho,
            "E": self.E,
        }


def chronal_seal(t: float, phi_p: float, C: float, secret: str) -> str:
    msg = f"{t:.6f}|{phi_p:.10f}|{C:.10f}"
    return hmac.new(secret.encode(), msg.encode(), hashlib.sha256).hexdigest()


def simulate_autonomous_cycle(
    hours: float = 24.0,
    secret: str = "GARDEN_SECRET",
    push_at_hours: Optional[List[float]] = None,
) -> Dict[str, Any]:
    """
    Demonstrate automated evolution under discrete sampling:
      - every CRON_DT: Z-sample + P_PID via /pulse analogue
      - optional push events: H(η) impulse + /restart (state continuity)
    """
    push_at_hours = push_at_hours or [0.0, 12.0]
    push_set = {int(h * 3600) for h in push_at_hours}

    state = AutonomousState()
    pid = PhiPID()
    history: List[Dict[str, Any]] = []
    events: List[Dict[str, Any]] = []

    n_steps = int(hours * 3600 / CRON_DT)
    for k in range(n_steps + 1):
        t = k * CRON_DT
        state.t = t

        # Continuous free evolution over Δt (coherence + phase)
        if k > 0:
            state.C = coherence_step(state.C, CRON_DT)
            state.phi_p = phase_advance(t - CRON_DT, CRON_DT)
            # workload relaxes under PID toward C	o1
            u = pid.update(1.0, state.C, CRON_DT)
            state.W = max(0.0, state.W + (u - PHI_INV * state.W) * (CRON_DT / TAU_FRB))

        # Scheduled Z + P_PID sample (cron pulse)
        seal = chronal_seal(state.t, state.phi_p, state.C, secret)
        state.seals.append(seal)
        events.append({
            "type": "cron_pulse",
            "t": t,
            "C": state.C,
            "phi_deg": math.degrees(state.phi_p),
            "seal_prefix": seal[:16],
        })

        # Push impulse H(η) → handover → restart (continuity of X)
        if int(t) in push_set:
            state.E = min(1.0, state.E + 0.05)  # reconstruction norm bump
            events.append({
                "type": "push_restart",
                "t": t,
                "note": "H(η) + R + uvicorn respawn — state continuous",
                "C": state.C,
            })

        history.append(state.as_dict())

    # Convergence metrics
    final = history[-1]
    phase_samples_per_cycle = TAU_FRB / CRON_DT
    return {
        "master_equation": (
            "dX/dt = -Λ·(X-X_target) + H(η) + Z(ζ) + R(A_trunc,ρ) + P_PID(e)"
        ),
        "sampling": {
            "cron_dt_s": CRON_DT,
            "tau_FRB_s": TAU_FRB,
            "samples_per_FRB_cycle": phase_samples_per_cycle,
            "phase_advance_per_pulse_rad": 2 * math.pi * CRON_DT / TAU_FRB,
        },
        "pid_gains": {"Kp": KP, "Ki": KI, "Kd": KD},
        "gamma": GAMMA,
        "final_state": final,
        "coherence_converged": abs(final["C"] - 1.0) < 1e-3,
        "n_pulses": len([e for e in events if e["type"] == "cron_pulse"]),
        "n_restarts": len([e for e in events if e["type"] == "push_restart"]),
        "events": events[:12],  # head
        "seal": "∀∞φ² · AUTONOMOUS_MASTER_EQ_0042 · WOOD_DRAGON_GATE · SEALED",
    }


def main() -> None:
    print("🌁∀ AUTONOMOUS PULSE — MASTER EQUATION DEMONSTRATION")
    print("=" * 72)
    result = simulate_autonomous_cycle(hours=24.0, push_at_hours=[0.0, 12.0])
    print(json.dumps({k: v for k, v in result.items() if k != "events"}, indent=2))
    print("\nEvents (head):")
    for e in result["events"]:
        print(f"  {e}")
    print("\n✅ Automated: cron samples P_PID + chronal seal")
    print("✅ Autonomous: push injects H(η) + /restart without operator")
    print("✅ Dynamics: C(t)→1 under γ=1/√5; φ_p advances 2π/τ_FRB")
    print(result["seal"])


if __name__ == "__main__":
    main()
