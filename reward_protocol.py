"""
reward_protocol.py

Scalar reward ("SPU") computation for the reward loop.

SPU is a normalized scalar in [0,1] aggregated from n sub-metrics m_i in [0,1]
with weights w_i >= 0, sum(w_i) == 1.

Three aggregation modes: linear, geometric, harmonic.

Pass/fail gate uses hysteresis (tau_lo < tau_hi) to prevent flapping.

Drift check compares online SPU against a sidecar-recomputed offline SPU.

The golden ratio appears only as a weight/threshold convention.
It is not a physical constant here.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

PHI = (1.0 + 5.0 ** 0.5) / 2.0


@dataclass(frozen=True)
class Gate:
    tau_hi: float = PHI ** -1   # ~0.618
    tau_lo: float = PHI ** -2   # ~0.382
    eps: float = 0.05


def phi_harmonic_weights(n: int) -> tuple[float, ...]:
    """Weights w_i proportional to phi^{-i}, normalized to sum to 1."""
    if n < 1:
        raise ValueError("n must be >= 1")
    raw = [PHI ** -(i + 1) for i in range(n)]
    s = sum(raw)
    return tuple(x / s for x in raw)


def spu(m: Sequence[float], w: Sequence[float], mode: str = "linear") -> float:
    """Aggregate metrics m with weights w. m_i must be in [0,1]."""
    if len(m) != len(w):
        raise ValueError("m and w must have equal length")
    if any(x < 0.0 or x > 1.0 for x in m):
        raise ValueError("metrics must lie in [0,1]")
    if abs(sum(w) - 1.0) > 1e-9:
        raise ValueError("weights must sum to 1")
    if mode == "linear":
        return sum(wi * mi for wi, mi in zip(w, m))
    if mode == "geometric":
        p = 1.0
        for wi, mi in zip(w, m):
            p *= mi ** wi
        return p
    if mode == "harmonic":
        if any(mi == 0.0 for mi in m):
            return 0.0
        return 1.0 / sum(wi / mi for wi, mi in zip(w, m))
    raise ValueError(f"unknown mode: {mode!r}")


def verdict(spu_on: float, spu_off: float, g: Gate) -> str:
    """Return one of PASS, FAIL, HOLD, DRIFT. Sidecar can only downgrade."""
    if abs(spu_on - spu_off) > g.eps:
        return "DRIFT"
    if spu_on >= g.tau_hi:
        return "PASS"
    if spu_on <= g.tau_lo:
        return "FAIL"
    return "HOLD"


def bounded_reward(spu_value: float, budget: float) -> float:
    return budget * spu_value


def timescales_separated(rate_L1: float, rate_L2: float, rate_L3: float) -> bool:
    """Rates are iterations per second. Outer loop must be strictly slower."""
    return rate_L3 <= 0.1 * rate_L2 <= 0.01 * rate_L1
