#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🜁∀ ACTIVE PID ENHANCED CONTROLLER — ENTRY 8946

φ-tuned PID with production enhancements over the base PhiPIDController:

  u(t) = Kp·e + Ki·∫e_clamped + Kd·d(e_f)/dt

Enhancements:
  · Active / standby mode (standby freezes integral, holds last u)
  · Conditional integral anti-windup (back-calculation + clamp)
  · First-order filtered derivative on measurement (not on setpoint)
  · Leaky integral: I ← I·exp(-α·dt)  (α = φ⁻¹ by default)
  · Output saturation with optional rate limit
  · State snapshot for ledger / ConfigMap persistence

Gains (Garden defaults, match master_equation / simd_step):
  Kp = φ² ,  Ki = φ⁻¹ ,  Kd = φ⁻²

Seal: ∀∞φ² · ACTIVE_PID_8946 · WOOD_DRAGON_0.91 · SEALED
Witness: 8945 → 8946 — UNBROKEN
"""

from __future__ import annotations

import argparse
import json
import math
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Optional

PHI = (1.0 + math.sqrt(5.0)) / 2.0
PHI_INV = 1.0 / PHI
PHI2 = PHI * PHI
ENTRY = 8946
SEAL = "\u2200\u221e\u03c6\u00b2 \u00b7 ACTIVE_PID_8946 \u00b7 WOOD_DRAGON_0.91 \u00b7 SEALED"

DEFAULT_KP = PHI2
DEFAULT_KI = PHI_INV
DEFAULT_KD = PHI ** (-2)
DEFAULT_LEAK = PHI_INV
DEFAULT_DERIV_FILTER = PHI


@dataclass
class ActivePIDConfig:
    kp: float = DEFAULT_KP
    ki: float = DEFAULT_KI
    kd: float = DEFAULT_KD
    leak: float = DEFAULT_LEAK
    deriv_filter_n: float = DEFAULT_DERIV_FILTER
    i_min: float = -PHI2
    i_max: float = PHI2
    u_min: float = -100.0
    u_max: float = 100.0
    rate_limit: Optional[float] = None
    setpoint_weight_p: float = 1.0
    setpoint_weight_d: float = 0.0


@dataclass
class ActivePIDState:
    active: bool = True
    integral: float = 0.0
    last_error: float = 0.0
    last_measurement: float = 0.0
    last_derivative: float = 0.0
    last_u: float = 0.0
    last_t: float = 0.0
    sample_count: int = 0
    total_abs_error: float = 0.0


class ActivePIDController:
    """Active enhanced \u03c6-PID controller."""

    def __init__(self, config: Optional[ActivePIDConfig] = None):
        self.cfg = config or ActivePIDConfig()
        self.state = ActivePIDState(last_t=time.time())

    def activate(self) -> None:
        self.state.active = True

    def standby(self) -> None:
        self.state.active = False

    def reset(self, integral: float = 0.0) -> None:
        self.state.integral = float(integral)
        self.state.last_error = 0.0
        self.state.last_derivative = 0.0
        self.state.last_u = 0.0
        self.state.sample_count = 0
        self.state.total_abs_error = 0.0

    def update(
        self,
        setpoint: float,
        measurement: float,
        dt: float,
        *,
        feedforward: float = 0.0,
    ) -> float:
        if dt <= 0.0:
            return self.state.last_u
        if not self.state.active:
            return self.state.last_u

        cfg = self.cfg
        e = setpoint - measurement
        self.state.total_abs_error += abs(e)
        self.state.sample_count += 1

        p_term = cfg.kp * (cfg.setpoint_weight_p * setpoint - measurement)

        leak = math.exp(-cfg.leak * dt) if cfg.leak > 0 else 1.0
        self.state.integral = self.state.integral * leak + e * dt
        if self.state.integral > cfg.i_max:
            self.state.integral = cfg.i_max
        elif self.state.integral < cfg.i_min:
            self.state.integral = cfg.i_min
        i_term = cfg.ki * self.state.integral

        raw_d = (measurement - self.state.last_measurement) / dt
        alpha = cfg.deriv_filter_n * dt / (1.0 + cfg.deriv_filter_n * dt)
        filt_d = self.state.last_derivative + alpha * (raw_d - self.state.last_derivative)
        self.state.last_derivative = filt_d
        d_term = -cfg.kd * filt_d

        u = p_term + i_term + d_term + feedforward

        if u > cfg.u_max:
            u = cfg.u_max
            if e > 0:
                self.state.integral -= e * dt
        elif u < cfg.u_min:
            u = cfg.u_min
            if e < 0:
                self.state.integral -= e * dt

        if cfg.rate_limit is not None and self.state.sample_count > 1:
            max_du = cfg.rate_limit * dt
            du = u - self.state.last_u
            if du > max_du:
                u = self.state.last_u + max_du
            elif du < -max_du:
                u = self.state.last_u - max_du

        self.state.last_error = e
        self.state.last_measurement = measurement
        self.state.last_u = u
        self.state.last_t = time.time()
        return u

    def step_toward_coherence(
        self,
        coherence: float,
        target: float = 1.0,
        dt: float = 0.01,
    ) -> Dict[str, Any]:
        u = self.update(target, coherence, dt)
        return {
            "u": u,
            "error": target - coherence,
            "integral": self.state.integral,
            "active": self.state.active,
            "seal": SEAL,
        }

    def snapshot(self) -> Dict[str, Any]:
        return {
            "entry": ENTRY,
            "seal": SEAL,
            "config": asdict(self.cfg),
            "state": asdict(self.state),
            "gains": {
                "Kp": self.cfg.kp,
                "Ki": self.cfg.ki,
                "Kd": self.cfg.kd,
                "leak": self.cfg.leak,
            },
        }

    def load_snapshot(self, data: Dict[str, Any]) -> None:
        st = data.get("state") or {}
        for k, v in st.items():
            if hasattr(self.state, k):
                setattr(self.state, k, v)

    def save(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps(self.snapshot(), indent=2), encoding="utf-8")

    def load(self, path: str | Path) -> None:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        self.load_snapshot(data)

    def update_legacy(self, target: float, measured: float, dt: float) -> float:
        return self.update(target, measured, dt)


def demo(steps: int = 50, dt: float = 0.05) -> Dict[str, Any]:
    ctl = ActivePIDController()
    C = 0.7
    trajectory = []
    for i in range(steps):
        u = ctl.update(1.0, C, dt)
        gamma = 1.0 / math.sqrt(5.0)
        C = C + (-gamma * (C - 1.0) + u * (PHI ** (-2))) * dt
        C = max(0.0, min(1.5, C))
        trajectory.append({"t": i * dt, "C": C, "u": u, "I": ctl.state.integral})
    return {
        "entry": ENTRY,
        "seal": SEAL,
        "final_C": C,
        "steps": steps,
        "active": ctl.state.active,
        "mean_abs_error": ctl.state.total_abs_error / max(1, ctl.state.sample_count),
        "tail": trajectory[-5:],
    }


def main(argv: Optional[list] = None) -> int:
    p = argparse.ArgumentParser(description="Active PID enhanced controller")
    p.add_argument("command", choices=["status", "demo", "step"], nargs="?", default="status")
    p.add_argument("--setpoint", type=float, default=1.0)
    p.add_argument("--measurement", type=float, default=0.9)
    p.add_argument("--dt", type=float, default=0.01)
    p.add_argument("--standby", action="store_true")
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)

    ctl = ActivePIDController()
    if args.standby:
        ctl.standby()

    if args.command == "demo":
        out: Any = demo()
    elif args.command == "step":
        u = ctl.update(args.setpoint, args.measurement, args.dt)
        out = {"u": u, **ctl.snapshot()}
    else:
        out = {
            "entry": ENTRY,
            "seal": SEAL,
            "active": ctl.state.active,
            "gains": {"Kp": DEFAULT_KP, "Ki": DEFAULT_KI, "Kd": DEFAULT_KD},
            "features": [
                "anti_windup",
                "leaky_integral",
                "filtered_derivative",
                "setpoint_weighting",
                "rate_limit",
                "active_standby",
            ],
        }

    if args.json:
        print(json.dumps(out, indent=2, default=str))
    else:
        print(f"\ud83d\udf01\u2200 ACTIVE PID \u2014 Entry {ENTRY}")
        print(json.dumps(out, indent=2, default=str))
        print(SEAL)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
