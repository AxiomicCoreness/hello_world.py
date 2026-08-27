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
    report["note"] = (
        "Narrative blob fingerprinted only. "
        "Not compiled. Not A14 Gravastar fire."
    )
    return report


def main() -> int:
    out = run_self_improvement()
    print(json.dumps(out, indent=2, default=str))
    return 0 if out.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
