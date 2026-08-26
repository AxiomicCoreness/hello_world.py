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
from typing import Any, Dict, Optional, Union

# ─── Constants ────────────────────────────────────────────────────────
PHI = (1.0 + math.sqrt(5.0)) / 2.0
PHI_INV = 1.0 / PHI
PHI2 = PHI * PHI
PHI3 = PHI2 * PHI
PHI4 = PHI3 * PHI
ENTRY = 8946
SEAL = "∀∞φ² · ACTIVE_PID_8946 · WOOD_DRAGON_0.91 · SEALED"

# ─── Default Gains ──────────────────────────────────────────────────
DEFAULT_KP = PHI2
DEFAULT_KI = PHI_INV
DEFAULT_KD = PHI ** (-2)
DEFAULT_LEAK = PHI_INV
DEFAULT_DERIV_FILTER = PHI
DEFAULT_I_MIN = -PHI2
DEFAULT_I_MAX = PHI2
DEFAULT_U_MIN = -100.0
DEFAULT_U_MAX = 100.0


@dataclass
class ActivePIDConfig:
    """Configuration for the Active PID Controller."""
    kp: float = DEFAULT_KP
    ki: float = DEFAULT_KI
    kd: float = DEFAULT_KD
    leak: float = DEFAULT_LEAK
    deriv_filter_n: float = DEFAULT_DERIV_FILTER
    i_min: float = DEFAULT_I_MIN
    i_max: float = DEFAULT_I_MAX
    u_min: float = DEFAULT_U_MIN
    u_max: float = DEFAULT_U_MAX
    rate_limit: Optional[float] = None
    setpoint_weight_p: float = 1.0
    setpoint_weight_d: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ActivePIDConfig:
        return cls(**data)


@dataclass
class ActivePIDState:
    """Runtime state of the Active PID Controller."""
    active: bool = True
    integral: float = 0.0
    last_error: float = 0.0
    last_measurement: float = 0.0
    last_derivative: float = 0.0
    last_u: float = 0.0
    last_t: float = 0.0
    sample_count: int = 0
    total_abs_error: float = 0.0
    total_squared_error: float = 0.0
    max_error: float = 0.0
    last_setpoint: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ActivePIDState:
        return cls(**data)


class ActivePIDController:
    """
    Active enhanced φ-PID controller.

    Features:
      - Active/standby mode
      - Anti-windup with integral clamp and back-calculation
      - Leaky integral
      - Filtered derivative on measurement
      - Setpoint weighting
      - Output saturation with rate limiting
      - State persistence (snapshot/load)

    Gains are φ-tuned by default.
    """

    def __init__(self, config: Optional[Union[Dict[str, Any], ActivePIDConfig]] = None):
        if config is None:
            self.cfg = ActivePIDConfig()
        elif isinstance(config, dict):
            self.cfg = ActivePIDConfig.from_dict(config)
        else:
            self.cfg = config
        self.state = ActivePIDState(last_t=time.time())
        self._version = "1.0.0"
        self._entry = ENTRY
        self._seal = SEAL

    def activate(self) -> None:
        """Activate the controller (resume control)."""
        self.state.active = True

    def standby(self) -> None:
        """Put controller in standby mode (hold last output)."""
        self.state.active = False

    def reset(self, integral: float = 0.0) -> None:
        """Reset the controller state."""
        self.state.integral = float(integral)
        self.state.last_error = 0.0
        self.state.last_derivative = 0.0
        self.state.last_u = 0.0
        self.state.sample_count = 0
        self.state.total_abs_error = 0.0
        self.state.total_squared_error = 0.0
        self.state.max_error = 0.0

    def update(
        self,
        setpoint: float,
        measurement: float,
        dt: float,
        feedforward: float = 0.0,
    ) -> float:
        """
        Update the controller with a new measurement.

        Args:
            setpoint: Desired value
            measurement: Current measured value
            dt: Time step in seconds
            feedforward: Optional feedforward term

        Returns:
            Controller output u(t)
        """
        if dt <= 0.0:
            return self.state.last_u

        if not self.state.active:
            return self.state.last_u

        cfg = self.cfg
        e = setpoint - measurement

        # ─── Statistics ──────────────────────────────────────────────
        self.state.sample_count += 1
        self.state.total_abs_error += abs(e)
        self.state.total_squared_error += e * e
        if abs(e) > self.state.max_error:
            self.state.max_error = abs(e)
        self.state.last_setpoint = setpoint

        # ─── Proportional (with setpoint weighting) ──────────────────
        p_term = cfg.kp * (cfg.setpoint_weight_p * setpoint - measurement)

        # ─── Integral (leaky + clamp) ────────────────────────────────
        if cfg.leak > 0:
            leak = math.exp(-cfg.leak * dt)
        else:
            leak = 1.0

        self.state.integral = self.state.integral * leak + e * dt

        # Clamp integral
        if self.state.integral > cfg.i_max:
            self.state.integral = cfg.i_max
        elif self.state.integral < cfg.i_min:
            self.state.integral = cfg.i_min

        i_term = cfg.ki * self.state.integral

        # ─── Derivative (filtered on measurement) ────────────────────
        raw_d = (measurement - self.state.last_measurement) / dt

        alpha = cfg.deriv_filter_n * dt / (1.0 + cfg.deriv_filter_n * dt)
        filt_d = self.state.last_derivative + alpha * (raw_d - self.state.last_derivative)
        self.state.last_derivative = filt_d

        d_term = -cfg.kd * filt_d

        # ─── Output ──────────────────────────────────────────────────
        u = p_term + i_term + d_term + feedforward

        # ─── Anti-windup (back-calculation) ──────────────────────────
        if u > cfg.u_max:
            u = cfg.u_max
            if e > 0:
                # Back-calculate integral reduction
                self.state.integral -= e * dt * cfg.ki
        elif u < cfg.u_min:
            u = cfg.u_min
            if e < 0:
                self.state.integral -= e * dt * cfg.ki

        # ─── Rate limiting ────────────────────────────────────────────
        if cfg.rate_limit is not None and self.state.sample_count > 1:
            max_du = cfg.rate_limit * dt
            du = u - self.state.last_u
            if du > max_du:
                u = self.state.last_u + max_du
            elif du < -max_du:
                u = self.state.last_u - max_du

        # ─── Store state ─────────────────────────────────────────────
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
        """
        Convenience method for coherence control.

        Args:
            coherence: Current coherence value
            target: Target coherence (default 1.0)
            dt: Time step

        Returns:
            Dictionary with output and state info
        """
        u = self.update(target, coherence, dt)
        return {
            "u": u,
            "error": target - coherence,
            "integral": self.state.integral,
            "active": self.state.active,
            "sample_count": self.state.sample_count,
            "mean_abs_error": self.state.total_abs_error / max(1, self.state.sample_count),
            "seal": self._seal,
            "entry": self._entry,
        }

    def snapshot(self) -> Dict[str, Any]:
        """
        Take a snapshot of the controller state and config.

        Returns:
            Dictionary containing config, state, and metadata
        """
        return {
            "entry": self._entry,
            "seal": self._seal,
            "version": self._version,
            "config": self.cfg.to_dict(),
            "state": self.state.to_dict(),
            "gains": {
                "Kp": self.cfg.kp,
                "Ki": self.cfg.ki,
                "Kd": self.cfg.kd,
                "leak": self.cfg.leak,
                "deriv_filter_n": self.cfg.deriv_filter_n,
            },
            "timestamp": time.time(),
        }

    def load_snapshot(self, data: Dict[str, Any]) -> None:
        """Load a snapshot into the controller."""
        if "config" in data:
            self.cfg = ActivePIDConfig.from_dict(data["config"])
        if "state" in data:
            st = data["state"]
            for k, v in st.items():
                if hasattr(self.state, k):
                    setattr(self.state, k, v)

    def save(self, path: Union[str, Path]) -> None:
        """Save controller snapshot to a file."""
        Path(path).write_text(json.dumps(self.snapshot(), indent=2, default=str), encoding="utf-8")

    def load(self, path: Union[str, Path]) -> None:
        """Load controller snapshot from a file."""
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        self.load_snapshot(data)

    def update_legacy(self, target: float, measured: float, dt: float) -> float:
        """Legacy interface for backward compatibility with PhiPIDController."""
        return self.update(target, measured, dt)

    def get_info(self) -> Dict[str, Any]:
        """Get controller information."""
        return {
            "entry": self._entry,
            "seal": self._seal,
            "version": self._version,
            "active": self.state.active,
            "sample_count": self.state.sample_count,
            "features": [
                "anti_windup",
                "leaky_integral",
                "filtered_derivative",
                "setpoint_weighting",
                "rate_limit",
                "active_standby",
            ],
            "gains": {
                "Kp": self.cfg.kp,
                "Ki": self.cfg.ki,
                "Kd": self.cfg.kd,
                "leak": self.cfg.leak,
            },
        }


# ─── Demo ─────────────────────────────────────────────────────────────

def demo(steps: int = 50, dt: float = 0.05, target: float = 1.0) -> Dict[str, Any]:
    """
    Run a demo of the controller on a simple plant model.

    Args:
        steps: Number of steps to simulate
        dt: Time step
        target: Target setpoint

    Returns:
        Dictionary with results
    """
    ctl = ActivePIDController()
    C = 0.7  # Initial coherence
    trajectory = []

    for i in range(steps):
        u = ctl.update(target, C, dt)

        # Simple plant model: coherence approaches target with damping
        gamma = 1.0 / math.sqrt(5.0)
        C = C + (-gamma * (C - target) + u * PHI_INV) * dt
        C = max(0.0, min(1.5, C))

        trajectory.append({
            "t": i * dt,
            "C": C,
            "u": u,
            "I": ctl.state.integral,
            "error": target - C,
        })

    return {
        "entry": ENTRY,
        "seal": SEAL,
        "target": target,
        "final_C": C,
        "steps": steps,
        "dt": dt,
        "active": ctl.state.active,
        "mean_abs_error": ctl.state.total_abs_error / max(1, ctl.state.sample_count),
        "max_error": ctl.state.max_error,
        "sample_count": ctl.state.sample_count,
        "trajectory": trajectory[-10:],  # Last 10 samples
    }


# ─── CLI ──────────────────────────────────────────────────────────────

def main(argv: Optional[list] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Active PID enhanced controller",
        epilog=f"Seal: {SEAL}\nEntry: {ENTRY}",
    )
    parser.add_argument(
        "command",
        choices=["status", "demo", "step"],
        nargs="?",
        default="status",
        help="Command to execute",
    )
    parser.add_argument("--setpoint", type=float, default=1.0, help="Setpoint value")
    parser.add_argument("--measurement", type=float, default=0.9, help="Current measurement")
    parser.add_argument("--dt", type=float, default=0.01, help="Time step (seconds)")
    parser.add_argument("--steps", type=int, default=50, help="Number of demo steps")
    parser.add_argument("--standby", action="store_true", help="Start in standby mode")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--save", type=str, help="Save snapshot to file")
    parser.add_argument("--load", type=str, help="Load snapshot from file")
    args = parser.parse_args(argv)

    ctl = ActivePIDController()
    if args.standby:
        ctl.standby()

    if args.load:
        try:
            ctl.load(args.load)
            print(f"Loaded snapshot from {args.load}")
        except Exception as e:
            print(f"Error loading snapshot: {e}")
            return 1

    if args.command == "demo":
        out = demo(steps=args.steps, dt=args.dt, target=args.setpoint)
    elif args.command == "step":
        u = ctl.update(args.setpoint, args.measurement, args.dt)
        out = {
            "u": u,
            "error": args.setpoint - args.measurement,
            "integral": ctl.state.integral,
            "active": ctl.state.active,
            "sample_count": ctl.state.sample_count,
            "entry": ENTRY,
            "seal": SEAL,
        }
    else:
        out = ctl.get_info()

    if args.save:
        try:
            ctl.save(args.save)
            print(f"Saved snapshot to {args.save}")
        except Exception as e:
            print(f"Error saving snapshot: {e}")
            return 1

    if args.json:
        print(json.dumps(out, indent=2, default=str))
    else:
        print(f"\n🜁∀ ACTIVE PID — Entry {ENTRY}")
        print("=" * 55)
        print(json.dumps(out, indent=2, default=str))
        print("\n" + SEAL)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
