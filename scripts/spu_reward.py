#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SPU reward — minimal reference implementation (as-is).

See docs/spu_reward_loops.md for Mermaid diagrams and sidecar contract.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class Gate:
    tau_hi: float = 0.618
    tau_lo: float = 0.382
    eps: float = 0.05


def spu(m: Sequence[float], w: Sequence[float], mode: str = "linear") -> float:
    assert abs(sum(w) - 1.0) < 1e-9 and all(x >= 0 for x in m)
    if mode == "linear":
        return sum(wi * mi for wi, mi in zip(w, m))
    if mode == "geometric":
        p = 1.0
        for wi, mi in zip(w, m):
            p *= mi**wi
        return p
    if mode == "harmonic":
        return 1.0 / sum(wi / mi for wi, mi in zip(w, m))
    raise ValueError(mode)


def verdict(spu_on: float, spu_off: float, g: Gate) -> str:
    if abs(spu_on - spu_off) > g.eps:
        return "DRIFT"
    if spu_on >= g.tau_hi:
        return "PASS"
    if spu_on <= g.tau_lo:
        return "FAIL"
    return "HOLD"


if __name__ == "__main__":
    g = Gate()
    m = (0.9, 0.8, 0.7)
    w = (0.5, 0.3, 0.2)
    on = spu(m, w)
    off = spu(m, w)  # identical replay → no drift
    print(f"SPU_on={on:.6f} verdict={verdict(on, off, g)}")
