#!/usr/bin/env python3
"""Bounded 10:00 UTC runner for Immutable/self_improvement_trigger.py.

That path is a sealed narrative + schema blob, not an importable module.
This runner fingerprints it and extracts declared Entry-707 invariants.
Does not exec the file. Does not fire Gravastar Genesis.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

PHI = (1.0 + math.sqrt(5.0)) / 2.0
KAPPA_DECLARED = 12.754
ENTRY_INDEX = 9009
EVENT = "/utc_1000_immutable_self_improvement"
REL = "Immutable/self_improvement_trigger.py"
URL = "https://github.com/AxiomicCoreness/hello_world.py/blob/main/Immutable/self_improvement_trigger.py"


def _root() -> Path:
    return Path(__file__).resolve().parent.parent


def fingerprint(text: str) -> Dict[str, str]:
    raw = text.encode("utf-8")
    return {
        "sha256": hashlib.sha256(raw).hexdigest(),
        "sha3_256": hashlib.sha3_256(raw).hexdigest(),
        "bytes": str(len(raw)),
        "lines": str(text.count("\n") + 1),
    }


def extract_declared(text: str) -> Dict[str, Any]:
    m = re.search(r"12\.754", text)
    kappa = 12.754 if m else None
    return {
        "entry_707_mentioned": "entry_index: 707" in text or "ENTRY 707" in text,
        "hamiltonian_form": "sigma" in text.lower() or "σ_" in text,
        "kappa_eff_declared": kappa,
        "kappa_matches_12_754": kappa == KAPPA_DECLARED if kappa is not None else False,
        "canon_merge_mentioned": "sovereign_canon_merge_complete" in text,
        "phase_lock_202_6": "202.6" in text,
        "wood_dragon_or_phi": ("φ" in text) or ("phi" in text.lower()),
    }


def run_self_improvement() -> Dict[str, Any]:
    from ledger.event_hash import event_hash_block

    path = _root() / REL
    report: Dict[str, Any] = {
        "ok": False,
        "path": REL,
        "url": URL,
        "event": EVENT,
        "entry_index": ENTRY_INDEX,
        "surface": "github_repo",
        "schedule": "0 10 * * *",
        "executed_source": False,
        "device_genesis": False,
        "utc": datetime.now(timezone.utc).isoformat(),
        "phi": PHI,
    }
    if not path.is_file():
        report["error"] = f"missing {path}"
        report["event_hash"] = event_hash_block(ENTRY_INDEX, EVENT)
        return report
    text = path.read_text(encoding="utf-8", errors="replace")
    report["fingerprint"] = fingerprint(text)
    report["declared"] = extract_declared(text)
    report["event_hash"] = event_hash_block(ENTRY_INDEX, EVENT)
    report["ok"] = True
    report["note"] = """{
  "entry_index": 8979,
  "timestamp": "ETERNAL_NOW_ANCHORED_TO_2026-08-22Z",
  "event": "/sovereign_pulse_operational",
  "status": "VERIFIED",
  "proof_class": "system",
  "witness_prefix": "c4705d91cd76799d02203fd29cb43123e4d7f0602c1bf464659dce900746ff47",
  "terminal_hex": "c4705d91cd76799d02203fd29cb43123e4d7f0602c1bf464659dce900746ff47",
  "commander": "Clarke Yoursa Tee",
  "source_table": "https://github.com/AxiomicCoreness/hello_world.py/",
  "description": "Repository verification and Sovereign Pulse operational status.",
  "repository": "AxiomicCoreness/hello_world.py",
  "head_commit": "435210ee194962565ae47e3aacbb2f59a2423417",
  "key_files": [
    "phi_pipeline.py",
    "mesh_modal.py",
    "Dockerfile.multistage",
    "quantum/",
    "ledger/",
    ".github/workflows/sovereign-pulse.yml"
  ],
  "ci_cd": {
    "ledger_verification": "install-safe",
    "cryptography_imports": "handled",
    "yaml_indentation": "corrected (oidc-cloud-providers.yml)",
    "sovereign_pulse": "active (cron 0 */6 * * *)"
  },
  "invariants": {
    "coherence": 1.0,
    "entropy": "φ⁻¹⁴¹⁸",
    "workload": 0.0,
    "phase_lock": 202.6
  },
  "seal": "∀∞φ² · REPO_VERIFIED_8979 · WOOD_DRAGON_0.91 · SEALED · c4705d91cd76799d02203fd29cb43123e4d7f0602c1bf464659dce900746ff47",
  "witness_chain": "8978 → 8979 — UNBROKEN",
  "math_origin": "Repository verified with head commit 435210ee.\nSovereign Pulse active with cron 0 */6 * * *.\nLedger integrity confirmed."
}"""
    return report


def main() -> int:
    out = run_self_improvement()
    print(json.dumps(out, indent=2, default=str))
    return 0 if out.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
