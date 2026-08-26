#!/usr/bin/env python3
"""CI / workflow_dispatch entry adjacent to terminal.main().

Does not start the interactive menu or the unbounded Planck loop.
Hashes the dispatch event with hashlib.sha3_256 in ledger mathematical form.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import sys
from typing import Any, Dict

from quantum.deepseek_mesh.env import configure
from ledger.event_hash import event_hash_block


def dispatch_main(event: str = "/workflow_dispatch_terminal") -> Dict[str, Any]:
    env = configure()
    block = event_hash_block(9005, event)
    # hashlib close to main(): same domain-separated form used by the ledger
    digest = hashlib.sha3_256(
        (block["domain"] + "\x00" + block["payload"]).encode("utf-8")
    ).hexdigest()
    assert digest == block["hex"]
    out: Dict[str, Any] = {
        "ok": True,
        "entry": "quantum/deepseek_mesh/terminal.py",
        "call_site": "terminal_ci.dispatch_main → adjacent to terminal.main",
        "env": env,
        "event_hash": block,
        "phi": (1.0 + math.sqrt(5.0)) / 2.0,
        "ci": bool(os.getenv("CI") or os.getenv("TERMINAL_CI")),
    }
    try:
        from quantum.deepseek_mesh import terminal as term

        lattice = term.DonteLattice()
        engram = term.Engram5Layer()
        out["terminal_slice"] = {
            "donte_nodes": lattice.total_nodes,
            "donte_integrity": lattice.integrity_hash(),
            "engram_hash": engram.integrity_hash(),
            "sovereign_seal": getattr(term, "SOVEREIGN_SEAL", None),
            "skipped_main": True,
        }
    except Exception as exc:  # noqa: BLE001
        out["terminal_slice"] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    return out


def main() -> int:
    report = dispatch_main()
    print(json.dumps(report, indent=2, default=str))
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
