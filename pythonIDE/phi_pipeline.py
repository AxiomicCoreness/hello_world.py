#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
phi_pipeline.py — Grok node (grok-skill_tensor) pipeline + FIPS-202 gate

Landed on existing branch only. No ledger YAML write.

Rules:
  - FIPS-202 self-test (empty + abc); refuse on failure
  - ASCII hash alphabet labels: phi2 | delta | theta
  - Loopback policy: 127.0.0.1 (wildcard refused)
  - Digest for external verification; not auto-landed
  - MCP unfilled
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

PHI: float = (1.0 + math.sqrt(5.0)) / 2.0
PHI2: float = PHI * PHI
PHI3: float = PHI ** 3
PHASE_LOCK_DEG: float = 202.6
PHASE_LOCK_RAD: float = math.radians(PHASE_LOCK_DEG)
FRB_PERIOD_SECS: float = 78624.0
CORE_FREQ_HZ: float = 71.975

HASH_ALPHABET: Tuple[str, ...] = ("phi2", "delta", "theta")

# NIST FIPS-202 SHA3-256 (verified against hashlib.sha3_256)
_NIST_SHA3_256: Dict[str, str] = {
    "": (
        "a7ffc6f8bf1ed76651c14756a061d662"
        "f580ff4de43b49fa82d80a4b80f8434a"
    ),
    "abc": (
        "3a985da74fe225b2045c172d6bd390bd"
        "855f086e3e9d525b46bfe24511431532"
    ),
}


def _sha3_256_hex(data: bytes) -> str:
    return hashlib.sha3_256(data).hexdigest()


def fips_202_self_test() -> Tuple[bool, Dict[str, str]]:
    """Return (ok, observed). Do not land a seal when ok is False."""
    observed = {
        "": _sha3_256_hex(b""),
        "abc": _sha3_256_hex(b"abc"),
    }
    ok = all(observed[k] == _NIST_SHA3_256[k] for k in _NIST_SHA3_256)
    return ok, observed


@dataclass
class Stage:
    name: str
    fn: Callable[[Dict[str, Any]], Dict[str, Any]]


@dataclass
class PipelineResult:
    ok: bool
    stages: List[str] = field(default_factory=list)
    payload: Dict[str, Any] = field(default_factory=dict)
    digest: Optional[str] = None
    error: Optional[str] = None


def _stage_constants(ctx: Dict[str, Any]) -> Dict[str, Any]:
    ctx["phi"] = PHI
    ctx["phi2"] = PHI2
    ctx["phi3"] = PHI3
    ctx["phase_lock_deg"] = PHASE_LOCK_DEG
    ctx["phase_lock_rad"] = PHASE_LOCK_RAD
    ctx["frb_period_secs"] = FRB_PERIOD_SECS
    ctx["core_freq_hz"] = CORE_FREQ_HZ
    ctx["node"] = "grok-skill_tensor"
    ctx["agent"] = "grok"
    return ctx


def _stage_gate(ctx: Dict[str, Any]) -> Dict[str, Any]:
    ok, observed = fips_202_self_test()
    ctx["_gate_ok"] = ok
    ctx["_gate_observed"] = observed
    if not ok:
        raise RuntimeError(f"FIPS-202 self-test FAILED — refusing. observed={observed}")
    return ctx


def _stage_ascii_alphabet(ctx: Dict[str, Any]) -> Dict[str, Any]:
    ctx["hash_alphabet"] = list(HASH_ALPHABET)
    return ctx


def _stage_loopback(ctx: Dict[str, Any]) -> Dict[str, Any]:
    ctx["bind_host"] = "127.0.0.1"
    ctx["wildcard_refused"] = ["0.0.0.0", "::", "[::]"]
    return ctx


def _stage_digest(ctx: Dict[str, Any]) -> Dict[str, Any]:
    canonical = json.dumps(
        {k: v for k, v in ctx.items() if not k.startswith("_")},
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    ctx["_digest"] = _sha3_256_hex(canonical)
    return ctx


PIPELINE: List[Stage] = [
    Stage("constants", _stage_constants),
    Stage("fips_202_gate", _stage_gate),
    Stage("ascii_alphabet", _stage_ascii_alphabet),
    Stage("loopback", _stage_loopback),
    Stage("digest", _stage_digest),
]


def run_pipeline(initial: Optional[Dict[str, Any]] = None) -> PipelineResult:
    ctx: Dict[str, Any] = dict(initial or {})
    stages_done: List[str] = []
    for stage in PIPELINE:
        try:
            ctx = stage.fn(ctx)
            stages_done.append(stage.name)
        except Exception as e:
            return PipelineResult(
                ok=False,
                stages=stages_done,
                payload={k: v for k, v in ctx.items() if not k.startswith("_")},
                digest=None,
                error=f"{stage.name}: {e}",
            )
    return PipelineResult(
        ok=True,
        stages=stages_done,
        payload={k: v for k, v in ctx.items() if not k.startswith("_")},
        digest=ctx.get("_digest"),
        error=None,
    )


def _main(argv: List[str]) -> int:
    if "--self-test" in argv:
        ok, observed = fips_202_self_test()
        print(json.dumps({"ok": ok, "observed": observed, "node": "grok-skill_tensor"}, indent=2))
        return 0 if ok else 2
    if "--dry-run" in argv:
        result = run_pipeline()
        print(
            json.dumps(
                {
                    "ok": result.ok,
                    "stages": result.stages,
                    "digest": result.digest,
                    "error": result.error,
                    "payload_keys": sorted(result.payload.keys()),
                    "node": "grok-skill_tensor",
                },
                indent=2,
            )
        )
        return 0 if result.ok else 2
    print("phi_pipeline.py — node: grok-skill_tensor (Grok)")
    print("  --self-test   FIPS-202 canonical vectors")
    print("  --dry-run     full pipeline; no landing")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
