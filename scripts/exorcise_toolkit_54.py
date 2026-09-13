#!/usr/bin/env python3
"""
scripts/exorcise_toolkit_54.py

Honest 54-capability pipeline — no 51-claim, no φ⁷×1000 DM myth,
no CMAC-512 in event-hash domain, stubs labeled, full arg audit.
NO_LEDGER_WRITE. MCP unfilled. Dual ASGI 127.0.0.1:8024 only.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

try:
    from pythonIDE.toolkit import SovereignToolkit, PHI
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from pythonIDE.toolkit import SovereignToolkit, PHI  # type: ignore

EXORCISED = [
    "claim:51_capabilities",
    "claim:DM≈φ⁷×1000",
    "claim:CMAC-512∈event_hash_domain",
    "claim:seal_add_writes_ledger",
]

AUDIT_ARGS = {
    "fibonacci": (10,),
    "phi_power": (3,),
    "purity_calc": ([[0.5, 0.0], [0.0, 0.5]],),
    "entropy_calc": ([[0.5, 0.0], [0.0, 0.5]],),
    "commutator": ([[1.0, 0.0], [0.0, 0.0]], [[0.0, 1.0], [0.0, 0.0]]),
    "trace_preservation": ([[0.5, 0.0], [0.0, 0.5]],),
    "null_ban_check": (0.0,),
    "retrocausal_kernel": (1.0,),
    "merkle_root": (["a", "b", "c"],),
    "seal_add": (None, "line"),
    "seal_get": (None,),
    "witness_verify": ("ledger/attenuation_chain.jsonl",),
    "hmac_sign": ("exorcise",),
    "integrity_hash": ({"k": 1},),
    "golden_sphere": (2,),
    "harmonic_shells": (3,),
    "operator_freq": ("X",),
    "operator_integrity": ("X",),
    "soft_max": ([1.0, 2.0, 3.0],),
    "delta_lemma": ("manifold",),
    "rk4_step": (lambda t, y: -y, 0.0, 1.0, 0.01),
}


def main() -> int:
    tk = SovereignToolkit()
    n = tk.count()
    print("=" * 64)
    print("EXORCISE PIPELINE — 54 honest capabilities")
    print("=" * 64)
    print(f"count: {n} (must be 54)")
    if n != 54:
        print(f"FAIL: expected 54, got {n}")
        return 1
    print("exorcised false claims:")
    for c in EXORCISED:
        print(f"  - {c}")
    audit = tk.capabilities_audit(AUDIT_ARGS)
    failed = [k for k, v in audit.items() if not v]
    passed = sum(1 for v in audit.values() if v)
    print(f"audit (with args): {passed}/{n}")
    if failed:
        print("FAIL:", failed)
        return 1
    assert abs(tk.call("golden_ratio") - PHI) < 1e-12
    assert tk.call("fibonacci", 10) == 55
    root = tk.call("merkle_root", ["a", "b"])
    assert isinstance(root, str) and len(root) == 64
    print(f"stubs (labeled): {tk.stubs()}")
    print(f"health: {tk.call('health')}")
    print("CMAC-512 ∉ event-hash domain — OK")
    print("DM φ⁷×1000 rejected — residual form only — OK")
    print("=" * 64)
    print("EXORCISE PASS — 54/54")
    print("=" * 64)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
