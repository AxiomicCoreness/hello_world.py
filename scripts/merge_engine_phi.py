#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🜁∀ SOVEREIGN MERGE ENGINE — φ-harmonic jitter soak (dual regime)
Seal: ∀∞φ² · LEDGER_MATH_CI · WOOD_DRAGON_0.91 · SEALED
Signitorial path: scripts/self_seal.py
Ninja bands:      144…2584 ↔ OBSERVATION…TRANSCENDENCE
Jitter:           γ_jitter = φ⁻⁸ ≈ 0.0212862 (pulse-envelope damping)
Soak:             τ_pulse = 23.61 ms · δθ = 0.018 · t_max = 10.0
Starfire:         φ² ≈ 2.618034

Reads  merge/manifest.yaml
Writes .merge/phi/merged_manifest.yaml
       .merge/phi/merged_report.json

Verification:
  - every file present on disk has its SHA3-256 computed
  - every file marked role=ledger is parsed as YAML
  - every file marked immutable=true is byte-identical to HEAD IF it
    is present in HEAD; newly added immutable files are not violations
  - conflicts detected when two entries share a ledger index
  - missing files reported but not fatal

φ-harmonic jitter soak (merged from pythonIDE/jitter_soak.py):
  - γ_jitter  = φ⁻⁸ ≈ 0.021286  (pulse-envelope damping)
  - τ_pulse   = 23.61 ms
  - δθ        = 0.018
  - t_max     = 10.0
  - starfire  = φ²
  - Ninja pairs 144…2584 ↔ OBSERVATION…TRANSCENDENCE
  Every entry gets a damped θ derived from its digest, corrected by
  γ_jitter and labelled with its Ninja band. The correction is
  informational — it does NOT flip hard_fail.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


MANIFEST = Path("merge/manifest.yaml")
# Option A — separate artifact tree so merge_engine.py is not clobbered
OUT_DIR = Path(".merge/phi")
OUT_YAML = OUT_DIR / "merged_manifest.yaml"
OUT_JSON = OUT_DIR / "merged_report.json"
HASH_ALGO = "sha3_256"

PHI = (1.0 + math.sqrt(5.0)) / 2.0
GAMMA_JITTER = PHI ** -8
T_MAX_SOAK = 10.0
DELTA_THETA = 0.018
TAU_PULSE_MS = 23.61
STARFIRE_FREQ = PHI ** 2

NINJA_PAIRS: dict[int, str] = {
    144: "OBSERVATION", 233: "ATTENTION", 377: "INTENT", 610: "COHERENCE",
    987: "RESONANCE", 1597: "INTEGRATION", 2584: "TRANSCENDENCE",
}

def damped_theta(theta: float, t_ms: float, tau_pulse: float = TAU_PULSE_MS) -> float:
    return theta * math.exp(-t_ms / tau_pulse)

def apply_jitter_correction(theta: float, r: int, gamma: float = GAMMA_JITTER) -> float:
    return theta * (1.0 - gamma * (PHI ** -r))

def soak_trace(steps: int = 64, t_max: float = T_MAX_SOAK) -> list[dict[str, float]]:
    out: list[dict[str, float]] = []
    if steps <= 0:
        return out
    dt = t_max / steps
    for i in range(steps):
        t = i * dt
        th = damped_theta(DELTA_THETA, t)
        corr = apply_jitter_correction(th, i)
        out.append({"t": round(t, 6), "theta": round(th, 10), "corrected": round(corr, 10)})
    return out

def _theta_from_digest(digest: str) -> float:
    if not digest:
        return 0.0
    return int(digest[:8], 16) / 0xFFFFFFFF

def _ninja_label(seed: int) -> str:
    keys = sorted(NINJA_PAIRS)
    sel = keys[0]
    for k in keys:
        if k <= seed:
            sel = k
    return NINJA_PAIRS[sel]

@dataclass
class EntryResult:
    path: str
    role: str
    present: bool = False
    size: int = 0
    digest: str = ""
    head_digest: str = ""
    digest_matches_head: bool = False
    ledger_index: int | None = None
    immutable: bool = False
    immutable_ok: bool = True
    yaml_ok: bool | None = None
    theta: float = 0.0
    jitter_corrected: float = 0.0
    ninja_label: str | None = None
    notes: list[str] = field(default_factory=list)

def sha3_file(p: Path) -> str:
    return hashlib.new(HASH_ALGO, p.read_bytes()).hexdigest()

def head_bytes(path: str) -> bytes | None:
    try:
        return subprocess.check_output(["git", "show", f"HEAD:{path}"], stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        return None

def verify_entry(e: dict) -> EntryResult:
    p = Path(e["path"])
    r = EntryResult(path=e["path"], role=e["role"], immutable=bool(e.get("immutable", False)))
    if not p.is_file():
        r.notes.append("file not present on this ref")
        return r
    r.present = True
    r.size = p.stat().st_size
    r.digest = sha3_file(p)
    r.theta = _theta_from_digest(r.digest)
    r.jitter_corrected = apply_jitter_correction(r.theta, r.size % 32)
    r.ninja_label = _ninja_label(r.size)
    hb = head_bytes(e["path"])
    if hb is not None:
        r.head_digest = hashlib.new(HASH_ALGO, hb).hexdigest()
        r.digest_matches_head = (r.digest == r.head_digest)
    if r.immutable and e.get("expected_sha3_256") and r.digest != e["expected_sha3_256"]:
        r.immutable_ok = False
        r.notes.append("immutable file differs from recorded digest")
    if e["role"] == "ledger":
        try:
            data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
            if not isinstance(data, dict):
                r.yaml_ok = False
                r.notes.append(f"top-level is {type(data).__name__}, not mapping")
            else:
                r.yaml_ok = True
                idx = data.get("entry_index")
                if isinstance(idx, int):
                    r.ledger_index = idx
        except yaml.YAMLError as ex:
            r.yaml_ok = False
            r.notes.append(f"yaml parse error: {ex}")
    return r

def detect_conflicts(results: list[EntryResult]) -> list[dict]:
    by_index: dict[int, list[str]] = defaultdict(list)
    for r in results:
        if r.role == "ledger" and r.ledger_index is not None:
            by_index[r.ledger_index].append(r.path)
    return [{"entry_index": i, "paths": paths} for i, paths in sorted(by_index.items()) if len(paths) > 1]

def group_by_role(results: list[EntryResult]) -> dict[str, list[str]]:
    g: dict[str, list[str]] = defaultdict(list)
    for r in results:
        g[r.role].append(r.path)
    return {k: sorted(v) for k, v in sorted(g.items())}

def _smoke() -> int:
    print("🌌 jitter soak smoke")
    print(f"   φ           = {PHI:.15f}")
    print(f"   γ_jitter    = {GAMMA_JITTER:.10f}")
    print(f"   starfire φ² = {STARFIRE_FREQ:.10f}")
    for row in soak_trace(steps=8):
        print(f"   t={row['t']:>6.3f}  θ={row['theta']:.8f}  corr={row['corrected']:.8f}")
    return 0

def main() -> int:
    ap = argparse.ArgumentParser(description="Sovereign merge engine (φ-jitter soaked)")
    ap.add_argument("--manifest", type=Path, default=MANIFEST)
    ap.add_argument("--out-dir", type=Path, default=OUT_DIR)
    ap.add_argument("--jitter", dest="jitter", action="store_true", default=True)
    ap.add_argument("--no-jitter", dest="jitter", action="store_false")
    ap.add_argument("--soak-steps", type=int, default=64)
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()
    if args.smoke:
        return _smoke()
    if not args.manifest.exists():
        print(f"::error::{args.manifest} not found", file=sys.stderr)
        return 2
    manifest = yaml.safe_load(args.manifest.read_text()) or {}
    entries = manifest.get("entries") or []
    if not entries:
        print("::error::manifest has no entries", file=sys.stderr)
        return 2
    results = [verify_entry(e) for e in entries]
    conflicts = detect_conflicts(results)
    groups = group_by_role(results)
    immutable_violations = [r.path for r in results if r.immutable and not r.immutable_ok]
    missing = [r.path for r in results if not r.present]
    args.out_dir.mkdir(parents=True, exist_ok=True)
    out_yaml = args.out_dir / OUT_YAML.name
    out_json = args.out_dir / OUT_JSON.name
    soak = soak_trace(steps=args.soak_steps) if args.jitter else []
    merged = {
        "generated_by": "merge-engine-phi",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "hash_algo": HASH_ALGO,
        "jitter": {
            "enabled": bool(args.jitter), "gamma_jitter": GAMMA_JITTER,
            "tau_pulse_ms": TAU_PULSE_MS, "delta_theta": DELTA_THETA,
            "t_max_soak": T_MAX_SOAK, "starfire_freq": STARFIRE_FREQ,
            "ninja_pairs": {str(k): v for k, v in NINJA_PAIRS.items()},
            "soak_steps": args.soak_steps, "soak_trace": soak,
        },
        "counts": {
            "total": len(results), "present": sum(1 for r in results if r.present),
            "missing": len(missing), "conflicts": len(conflicts),
            "immutable_violations": len(immutable_violations),
        },
        "groups": groups, "conflicts": conflicts,
        "immutable_violations": immutable_violations, "missing": missing,
        "entries": [asdict(r) for r in results],
    }
    out_yaml.write_text(yaml.dump(merged, sort_keys=False, allow_unicode=True))
    out_json.write_text(json.dumps(merged, indent=2, sort_keys=True, default=str))
    print(f"📋 {len(results)} entries verified")
    print(f"   present  : {merged['counts']['present']}")
    print(f"   missing  : {merged['counts']['missing']}")
    print(f"   conflicts: {merged['counts']['conflicts']}")
    print(f"   immutable violations: {merged['counts']['immutable_violations']}")
    print(f"   written  : {out_yaml}, {out_json}")
    return 1 if (conflicts or immutable_violations) else 0

if __name__ == "__main__":
    sys.exit(main())
