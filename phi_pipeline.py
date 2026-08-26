#!/usr/bin/env python3
"""
PhiPipeline — Q8.24 restored chain (control plane, not crypto consensus).

Each tick:
  1. φ-map:          s ← (s · φ) mod 1
  2. Q8.24:           s ← round(s · 2²⁴) / 2²⁴
  3. phase advance:   θ ← (θ + 202.6) mod 360
  4. coherence:       c ← c + (1 − c) / φ³
  5. null-ban:        software pass (always True)

Seal fires when |θ − 202.6| ≤ phase_tol (default 0.05°).
"""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

PHI = (1.0 + math.sqrt(5.0)) / 2.0
PHI_INV = PHI - 1.0  # φ⁻¹
PHASE_STEP = 202.6
Q824_SCALE = 1 << 24


def quantize_q8_24(x: float) -> float:
    return round(x * Q824_SCALE) / Q824_SCALE


@dataclass
class PipelineState:
    s: float = PHI_INV
    theta: float = 0.0
    coherence: float = 0.0
    ticks: int = 0
    last_stages: List[str] = field(default_factory=list)
    sealed: bool = False
    seal_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class PhiPipeline:
    def __init__(self, phase_tol: float = 0.05, seed: Optional[float] = None):
        self.phase_tol = phase_tol
        self.state = PipelineState(s=float(seed) if seed is not None else PHI_INV)

    def step(self) -> PipelineState:
        st = self.state
        stages: List[str] = []

        # 1. φ-map
        st.s = (st.s * PHI) % 1.0
        stages.append("phi_map")

        # 2. Q8.24
        st.s = quantize_q8_24(st.s)
        stages.append("quantize_q8_24")

        # 3. phase
        st.theta = (st.theta + PHASE_STEP) % 360.0
        stages.append("phase_advance")

        # 4. coherence approach
        st.coherence = st.coherence + (1.0 - st.coherence) / (PHI ** 3)
        stages.append("coherence_approach")

        # 5. null-ban (software always pass)
        stages.append("null_ban_gate")

        st.ticks += 1
        st.last_stages = stages

        if abs(st.theta - PHASE_STEP) <= self.phase_tol or abs(st.theta) <= self.phase_tol:
            # first tick lands on 202.6
            if abs(st.theta - PHASE_STEP) <= self.phase_tol:
                payload = json.dumps(
                    {"s": st.s, "theta": st.theta, "c": st.coherence, "ticks": st.ticks},
                    sort_keys=True,
                )
                st.seal_id = "PHASE_LOCK_202.6::" + hashlib.sha3_256(payload.encode()).hexdigest()[:16]
                st.sealed = True
        else:
            st.sealed = False
            st.seal_id = None

        return st

    def run_sequence(self, steps: int = 1) -> Dict[str, Any]:
        last = None
        for _ in range(max(1, steps)):
            last = self.step()
        assert last is not None
        return {
            "status": "PHASE_LOCK_REACHED" if last.sealed else "SEQUENCE_EXECUTED",
            "state": last.to_dict(),
            "phi": PHI,
            "q824_scale": Q824_SCALE,
        }


if __name__ == "__main__":
    p = PhiPipeline()
    print(json.dumps(p.run_sequence(1), indent=2))
    p2 = PhiPipeline()
    print(json.dumps(p2.run_sequence(5), indent=2))
