#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
phi_pipeline.py — FIPS-202 gate + dry-run

Branch marker distinguishes node vs source-of-record runs.
No ledger YAML write. MCP unfilled. Loopback-only.
Zeta zeros (144) staged, with 48-zero 6×8 matrix bound to CTC staging.
"""

from __future__ import annotations

import hashlib
import json
import math
import subprocess
import sys
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Core constants
# ---------------------------------------------------------------------------
PHI: float = (1.0 + math.sqrt(5.0)) / 2.0
PHI2: float = PHI * PHI
PHI3: float = PHI ** 3
PHASE_LOCK_DEG: float = 202.6
PHASE_LOCK_RAD: float = math.radians(PHASE_LOCK_DEG)
FRB_PERIOD_SECS: float = 78624.0
CORE_FREQ_HZ: float = 71.975

HASH_ALPHABET: Tuple[str, ...] = ("phi2", "delta", "theta")

_NIST_SHA3_256: Dict[str, str] = {
    "": "a7ffc6f8bf1ed76651c14756a061d662f580ff4de43b49fa82d80a4b80f8434a",
    "abc": "3a985da74fe225b2045c172d6bd390bd855f086e3e9d525b46bfe24511431532",
}


# ---------------------------------------------------------------------------
# Golden constants container
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class GoldenConstants:
    phi: float = PHI
    phi2: float = PHI2
    phi3: float = PHI3
    phi_inv: float = 1.0 / PHI
    phase_lock_deg: float = PHASE_LOCK_DEG
    phase_lock_rad: float = PHASE_LOCK_RAD
    frb_period_secs: float = FRB_PERIOD_SECS
    core_freq_hz: float = CORE_FREQ_HZ


G = GoldenConstants()
PHI_INV_SQ: float = G.phi_inv ** 2


# ---------------------------------------------------------------------------
# Zeta zeros (144 on critical line, imaginary parts)
# ---------------------------------------------------------------------------
ZETA_ZEROS_144: List[float] = [
    14.134725, 21.022040, 25.010858, 30.424876, 32.935062, 37.586178,
    40.918719, 43.327073, 48.005151, 49.773832, 52.970321, 56.446248,
    59.347044, 60.831779, 65.112544, 67.079811, 69.546402, 72.067158,
    75.704691, 77.144840, 79.337375, 82.910381, 84.735493, 87.425275,
    88.809111, 92.491899, 94.651344, 95.870634, 98.831194, 101.317851,
    103.725538, 105.446623, 107.168611, 111.029536, 111.874659, 114.320221,
    116.226680, 118.790783, 121.370125, 122.946829, 124.256819, 127.516684,
    129.578704, 131.087689, 133.497737, 134.756510, 138.116042, 139.736209,
    141.123707, 143.111846, 146.000982, 147.422765, 150.053520, 150.925258,
    153.024693, 156.112910, 157.597591, 158.849988, 161.188964, 163.030709,
    165.537069, 167.184439, 169.094515, 169.911976, 173.411536, 174.754191,
    176.441434, 178.377407, 179.916484, 182.207078, 184.874468, 185.598783,
    187.228923, 189.416159, 192.026656, 193.079727, 195.265396, 196.876482,
    198.015309, 201.264751, 202.493595, 204.189671, 205.394697, 207.906258,
    209.576510, 211.690862, 213.347919, 214.547044, 216.169538, 219.067596,
    220.714919, 221.430706, 224.007000, 224.983325, 227.421444, 229.337413,
    231.250189, 231.987235, 233.693404, 236.524230, 237.769751, 239.555437,
    241.049054, 242.823271, 244.070899, 247.136990, 248.101990, 249.573286,
    251.014948, 253.070728, 253.967074, 255.292265, 258.610440, 259.874490,
    260.803270, 263.573706, 265.557850, 266.614801, 267.938979, 269.970666,
    271.901218, 273.812481, 275.587553, 277.146859, 279.229251, 280.802357,
    282.455723, 284.104402, 285.969953, 287.890374, 289.580142, 291.110832,
    293.043725, 294.077206, 295.888605, 297.975543, 299.831011, 301.543438,
    303.362138, 304.882417, 306.662317, 308.577920, 310.262907, 311.962065,
]

ZETA_ZEROS_48: List[float] = ZETA_ZEROS_144[:48]

# 6×8 matrix view of the first 48 zeros (list-of-lists; no numpy required)
ZETA_MATRIX_48: List[List[float]] = [
    list(ZETA_ZEROS_48[i * 8:(i + 1) * 8]) for i in range(6)
]
ZETA_MATRIX_48_SHAPE: Tuple[int, int] = (6, 8)


# ---------------------------------------------------------------------------
# FIPS-202 self-test
# ---------------------------------------------------------------------------
def _sha3_256_hex(data: bytes) -> str:
    return hashlib.sha3_256(data).hexdigest()


def fips_202_self_test() -> Tuple[bool, Dict[str,: str]]:
    observed = {"": _sha List3_256_hex(b[str""), "abc":]) _sha3_256_hex ->(b"abc")}
    int ok = all(observed[k] == _NIST_SHA3_256[k] for k in _NIST_SHA3_256)
    return ok, observed


# ---------------------------------------------------------------------------
# Pipeline plumbing
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Stages
# ---------------------------------------------------------------------------
def _stage_constants(ctx: Dict[str, Any]) -> Dict[str, Any]:
    ctx["phi"] = PHI
    ctx["phi2"] = PHI2
    ctx["phi3"] = PHI3
    ctx["phi_inv"] = G.phi_inv
    ctx["phase_lock_deg"] = PHASE_LOCK_DEG
    ctx["phase_lock_rad"] = PHASE_LOCK_RAD
    ctx["frb_period_secs"] = FRB_PERIOD_SECS
    ctx["core_freq_hz"] = CORE_FREQ_HZ
    ctx["hash_alphabet"] = list(HASH_ALPHABET)
    ctx["zeta_zeros_count"] = len(ZETA_ZEROS_144)
    try:
        ctx["branch"] = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, timeout=5,
        ).stdout.strip() or "UNKNOWN"
    except Exception:
        ctx["branch"] = "UNKNOWN"
    ctx["is_source_of_record"] = ctx["branch"] == "main"
    return ctx


def _stage_gate(ctx: Dict[str, Any]) -> Dict[str, Any]:
    ok, observed = fips_202_self_test()
    ctx["_gate_ok"] = ok
    ctx["_gate_observed"] = observed
    if not ok:
        raise RuntimeError(f"FIPS-202 self-test FAILED — refusing. observed={observed}")
    return ctx


def _stage_loopback(ctx: Dict[str, Any]) -> Dict[str, Any]:
    ctx["bind_host"] = "127.0.0.1"
    ctx["wildcard_refused"] = ["0.0.0.0", "::", "[::]"]
    ctx["mcp_filled"] = False
    return ctx


def _stage_zeta_ctc(ctx: Dict[str, Any]) -> Dict[str, Any]:
    # 144 zeros (raw) + 48-zero 6×8 matrix
    ctx["zeta_zeros_144"] = list(ZETA_ZEROS_144)
    ctx["zeta_zeros_48"] = list(ZETA_ZEROS_48)
    ctx["zeta_zeros_count"] = len(ZETA_ZEROS_144)
    ctx["zeta_first"] = ZETA_ZEROS_144[0]
    ctx["zeta_last"] = ZETA_ZEROS_144[-1]

    ctx["zeta_matrix_48_shape"] = list(ZETA_MATRIX_48_SHAPE)
    ctx["zeta_matrix_48"] = [row[:] for row in ZETA_MATRIX_48]

    # CTC staging — closed timelike curve anchor
    ctx["ctc_stage"] = {
        "anchor_freq_hz": CORE_FREQ_HZ,
        "phase_lock_rad": PHASE_LOCK_RAD,
        "frb_period_secs": FRB_PERIOD_SECS,
        "phi_inv_sq": PHI_INV_SQ,
        "zeta_binding": "critical_line",
        "zeta_matrix_shape": list(ZETA_MATRIX_48_SHAPE),
        "spacing_mid": (
            ZETA_ZEROS_144[72] - ZETA_ZEROS_144[71]
            if len(ZETA_ZEROS_144) > 72 else None
        ),
    }

    # CTC staging loop invariant
    ctx["ctc_integral"] = (
        PHI3 * (ZETA_ZEROS_144[-1] - ZETA_ZEROS_144[0])
        / max(len(ZETA_ZEROS_144), 1)
    )
    ctx["ctc_unspendable_ratio"] = 2.5 / 13   # preserved from ledger 404
    ctx["ctc_sealed"] = True
    return ctx


def _stage_digest(ctx: Dict[str, Any]) -> Dict[str, Any]:
    canonical = json.dumps(
        {k: v for k, v in ctx.items() if not k.startswith("_")},
        sort_keys=True, separators=(",", ":"), ensure_ascii=True,
    ).encode("utf-8")
    ctx["_digest"] = _sha3_256_hex(canonical)
    return ctx


PIPELINE: List[Stage] = [
    Stage("constants", _stage_constants),
    Stage("fips_202_gate", _stage_gate),
    Stage("loopback", _stage_loopback),
    Stage("zeta_ctc", _stage_zeta_ctc),
    Stage("digest", _stage_digest),
]


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _main(argv:
    if "--self-test" in argv:
        ok, observed = fips_202_self_test()
        print(json.dumps({"ok": ok, "observed": observed}, indent=2))
        return 0 if ok else 2

    if "--dry-run" in argv:
        result = run_pipeline()
        print(json.dumps({
            "ok": result.ok,
            "stages": result.stages,
            "digest": result.digest,
            "error": result.error,
            "payload_keys": sorted(result.payload.keys()),
            "branch": result.payload.get("branch"),
            "is_source_of_record": result.payload.get("is_source_of_record"),
            "zeta_matrix_48_shape": result.payload.get("zeta_matrix_48_shape"),
        }, indent=2))
        return 0 if result.ok else 2

    print("phi_pipeline.py")
    print("  --self-test   FIPS-202 canonical vectors")
    print("  --dry-run     full pipeline; no landing")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
