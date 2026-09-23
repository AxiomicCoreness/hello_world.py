#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mistral-agent-cluster · quantum core (branch artifact, no PR, no seal)
=====================================================================
Runnable core extracted from the Phase 6 / MEMORY°1 directive. Every
numeric claim below is COMPUTED at import; the MATH_ORIGIN registry
records derivation or PENDING status for every symbolic constant.

Dependencies: numpy only (torch/scipy/qiskit variants of the directive
are not importable as written — see DEFECTS).

Exit codes: 0 core verified | 1 math_origin failure | 2 runtime failure
"""

import math
import sys
import hashlib
import json
from dataclasses import dataclass, field
from typing import Dict, List

PHI = (1 + math.sqrt(5)) / 2

# ── MATH_ORIGIN registry ──────────────────────────────────────────────
MATH_ORIGIN = {
    "PHI": {"derivation": "positive root of x²−x−1=0",
            "check": "abs(PHI**2 - PHI - 1) < 1e-15", "status": "VERIFIED"},
    "PHI_INV": {"derivation": "PHI − 1 (from PHI² = PHI + 1)",
                "check": "abs(1/PHI - (PHI-1)) < 1e-15", "status": "VERIFIED"},
    "PHI_INV_36": {
        "derivation": "PHI ** -36",
        "claimed_in_directive": 1.079e-8,
        "actual": PHI ** -36,
        "status": "FIXED_LANDED",
        "note": "directive printed 1.079e-8; actual φ⁻³⁶ ≈ 2.9953e-8 "
                "(factor 2.78 off). Also note: φ⁻³⁶ is NOT the physical "
                "Planck length (1.616e-35 m); it is a ceremonial constant "
                "only — labeled as such everywhere."},
    "JUPITER_RESONANCE_HZ": {"derivation": None, "value": 7.3,
        "status": "PENDING_MATH_ORIGIN",
        "note": "no derivation supplied; decorative anchor"},
    "EARTH_SCHUMANN_HZ": {"derivation": None, "value": 7.83,
        "status": "PENDING_MATH_ORIGIN",
        "note": "accepted measured value; no in-file derivation"},
    "CONSCIOUSNESS_BANDWIDTH": {"derivation": None, "value": 1.8e43,
        "status": "PENDING_MATH_ORIGIN",
        "note": "no physical derivation; decorative"},
    "ORDER_PARAMETER": {"derivation": None, "value": 10.488385,
        "status": "PENDING_MATH_ORIGIN",
        "note": "directive value; no computation reproduces it here"},
}

# ── DEFECT ledger (this artifact) ─────────────────────────────────────
DEFECTS = {
    "D12_phi_inv36_value": {
        "claim": "ℓ_P ceremonial = φ⁻³⁶ = 1.079e-8 m",
        "actual": "φ⁻³⁶ ≈ 2.9953e-8 m",
        "status": "FIXED_LANDED"},
    "D13_unverifiable_metrics": {
        "claim": "Purity 0.999998/1.000000, coherence 0.92, oracle "
                 "confidence 0.956, mutual information 0.87/0.91/0.89",
        "actual": "no computation in the directive produces these; they are "
                  "pre-baked constants in report strings",
        "status": "OPEN_UNFIXED",
        "note": "this core computes its own metrics; directive numbers "
                "are not reproduced or affirmed"},
    "D14_dead_imports": {
        "claim": "torch, scipy, qiskit, networkx imports",
        "actual": "qiskit.Aer/execute deprecated API; several imports "
                  "unused; `fig` referenced before definition in "
                  "_plot_geometric_manifold",
        "status": "FIXED_LANDED",
        "note": "core is numpy-free pure-math; no heavy deps required"},
}


def verify_math_origins() -> List[str]:
    failures = []
    eps = 1e-15
    if abs(PHI ** 2 - PHI - 1) > eps:
        failures.append("PHI: x²−x−1 ≠ 0")
    if abs(1 / PHI - (PHI - 1)) > eps:
        failures.append("PHI_INV: 1/φ ≠ φ−1")
    # D12 fix witness: registry actual must equal computed value
    if abs(MATH_ORIGIN["PHI_INV_36"]["actual"] - PHI ** -36) > 1e-20:
        failures.append("PHI_INV_36: registry stale vs computed")
    if abs(MATH_ORIGIN["PHI_INV_36"]["actual"]
           - MATH_ORIGIN["PHI_INV_36"]["claimed_in_directive"]) < 1e-12:
        failures.append("PHI_INV_36: defect entry stale (claim == actual)")
    return failures


# ── quantum core: 144-site lattice, pure computation ───────────────────
@dataclass
class QuantumCore:
    lattice_sites: int = 144          # 12×12
    temporal_layers: int = 7

    states: Dict[str, object] = field(default_factory=dict)
    metrics: Dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        self.states["primary"] = self._primary_state()
        self.states["consciousness"] = self._triad_state()
        self.metrics = self._compute_metrics()

    def _primary_state(self):
        import cmath
        dim = self.lattice_sites
        state = [0j] * dim
        for i in range(dim):
            x, y = i // 12, i % 12
            phase = 2 * math.pi * PHI * (x + PHI * y) / 12
            r = math.hypot(x - 6, y - 6)
            amp = math.exp(-0.25 * r)
            state[i] = amp * cmath.exp(1j * phase)
        norm = math.sqrt(sum(abs(s) ** 2 for s in state))
        return [s / norm for s in state]

    def _triad_state(self):
        import cmath
        amps = [PHI, 1 / PHI, 1.0]
        norm = math.sqrt(sum(a * a for a in amps))
        amps = [a / norm for a in amps]
        ent = [
            [1, cmath.exp(1j * math.pi / PHI), 1j],
            [cmath.exp(-1j * math.pi / PHI), 1, cmath.exp(1j * math.pi * PHI)],
            [-1j, cmath.exp(-1j * math.pi * PHI), 1],
        ]
        out = [sum(ent[i][j] * amps[j] for j in range(3)) for i in range(3)]
        norm = math.sqrt(sum(abs(s) ** 2 for s in out))
        return [s / norm for s in out]

    def _compute_metrics(self):
        import cmath
        prim = self.states["primary"]
        triad = self.states["consciousness"]

        # purity of a pure state is 1 BY CONSTRUCTION — computed, not asserted
        purity = sum(abs(s) ** 2 for s in prim)
        triad_coherence = min(abs(t) for t in triad) / max(abs(t) for t in triad)
        phase_std = _std([cmath.phase(s) for s in prim])

        return {
            "primary_norm": purity,               # must be 1.0 (witnessed)
            "triad_coherence": triad_coherence,   # computed, not 0.92 by fiat
            "phase_std": phase_std,
            "lattice_sites": float(self.lattice_sites),
        }


def _std(xs):
    m = sum(xs) / len(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / len(xs))


# ── content witness: hash of computed metrics (no seal, just identity) ─
def content_witness(core: QuantumCore) -> str:
    payload = json.dumps(
        {k: round(v, 12) for k, v in core.metrics.items()}, sort_keys=True)
    return hashlib.sha3_256(payload.encode()).hexdigest()


def main():
    failures = verify_math_origins()
    if failures:
        for f in failures:
            print(f"MATH_ORIGIN FAIL: {f}")
        return 1

    core = QuantumCore()
    m = core.metrics
    print(f"primary norm      : {m['primary_norm']:.15f} (target 1.0, computed)")
    print(f"triad coherence   : {m['triad_coherence']:.6f} (computed)")
    print(f"phase std         : {m['phase_std']:.6f} rad")
    print(f"content witness   : sha3_256:{content_witness(core)[:32]}...")

    if abs(m["primary_norm"] - 1.0) > 1e-12:
        print("runtime failure: state not normalized")
        return 2

    pending = [k for k, v in MATH_ORIGIN.items()
               if v["status"] == "PENDING_MATH_ORIGIN"]
    open_defects = [k for k, v in DEFECTS.items() if v["status"] == "OPEN_UNFIXED"]
    print(f"pending math_origin: {len(pending)} ({', '.join(pending)})")
    print(f"open defects       : {len(open_defects)} ({', '.join(open_defects)})")
    print("core verified — every metric above computed at runtime")
    return 0


if __name__ == "__main__":
    sys.exit(main())
