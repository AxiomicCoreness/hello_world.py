#!/usr/bin/env python3
"""GitHub long-horizon analogue of Trigger_Gravastar_ClarkeYoursaTee.

Runs a bounded i/144 window on the repo (workflow_dispatch + schedule).
Does not claim A14 device Genesis. Does not start october_Q1.main().
"""
from __future__ import annotations

import json
import math
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

PHI = (1.0 + math.sqrt(5.0)) / 2.0
PHASE_LOCK_DEG = 202.6
ENTRY_INDEX = 9008
EVENT = "/workflow_dispatch_gravastar_long_horizon"
TRIGGER_NAME = "Trigger_Gravastar_ClarkeYoursaTee"
HORIZON_MAX = 144
DEFAULT_STEPS = 8


def _clamp_i(value: Any, default: int = 1) -> int:
    try:
        return max(1, min(HORIZON_MAX, int(value)))
    except (TypeError, ValueError):
        return default


def horizon_window(i_start: int, steps: int) -> List[int]:
    start = _clamp_i(i_start)
    n = _clamp_i(steps, DEFAULT_STEPS)
    return [((start - 1 + k) % HORIZON_MAX) + 1 for k in range(n)]


def tick(i: int) -> Dict[str, Any]:
    from Immutable.run_on_gravastar import execute_immutable

    slice_ = execute_immutable(i_of_144=i)
    return {
        "i": i,
        "parameter": f"{i}/144",
        "immutable_ok": bool(slice_.get("ok")),
        "immutable": {
            "ok": slice_.get("ok"),
            "ref": slice_.get("ref"),
            "theorems": slice_.get("theorems"),
            "zeta_zeros": slice_.get("zeta_zeros"),
            "donte_nodes": slice_.get("donte_nodes"),
            "eigenvalue_i": slice_.get("eigenvalue_i"),
            "mode": slice_.get("mode"),
            "error": slice_.get("error"),
        },
    }


def horizon_main(
    event: str = EVENT,
    i_start: Optional[int] = None,
    steps: Optional[int] = None,
) -> Dict[str, Any]:
    from ledger.event_hash import event_hash_block
    from quantum.gravastar_trigger import MAPPED_PORTS, get_status

    if i_start is None:
        i_start = _clamp_i(os.getenv("GRAVASTAR_I_START", os.getenv("GRAVASTAR_I_OF_144", "1")))
    if steps is None:
        steps = _clamp_i(os.getenv("GRAVASTAR_HORIZON_STEPS", str(DEFAULT_STEPS)), DEFAULT_STEPS)

    window = horizon_window(i_start, steps)
    ticks = [tick(i) for i in window]
    block = event_hash_block(ENTRY_INDEX, event)
    status = get_status()
    passed = sum(1 for t in ticks if t["immutable_ok"])
    return {
        "ok": passed == len(ticks),
        "surface": "github_repo",
        "device_genesis": False,
        "device_fire": False,
        "trigger_name": TRIGGER_NAME,
        "event": event,
        "entry_index": ENTRY_INDEX,
        "call_site": (
            "quantum.gravastar_horizon.horizon_main "
            "→ Immutable.execute_immutable (bounded) "
            "≠ A14 Trigger_Gravastar fire"
        ),
        "horizon": {
            "i_start": window[0] if window else i_start,
            "steps": len(window),
            "max": HORIZON_MAX,
            "window": window,
            "passed": passed,
        },
        "ports_mapped": [p["port"] for p in MAPPED_PORTS],
        "status_snapshot": {
            "active": status.get("active"),
            "trigger_count": status.get("trigger_count"),
            "phase_lock_deg": status.get("phase_lock_deg", PHASE_LOCK_DEG),
            "resonance_thz": status.get("resonance_thz"),
        },
        "ticks": ticks,
        "event_hash": block,
        "phi": PHI,
        "phase_lock_deg": PHASE_LOCK_DEG,
        "utc": datetime.now(timezone.utc).isoformat(),
        "ci": bool(os.getenv("CI") or os.getenv("GRAVASTAR_HORIZON")),
    }


def main() -> int:
    report = horizon_main()
    print(json.dumps(report, indent=2, default=str))
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
