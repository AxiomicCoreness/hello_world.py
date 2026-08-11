#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Wood Dragon Technique — Garden clarity cadence.

Rhythms:
  - wood_dragon_period_days = 0.91   (short pulse / clarity pass)
  - deep_space_period_days  = 16.35  (synchronizer beat)

run_wood_dragon_technique() validates latest symplectic_status.json
(if present) and returns a rhythm report for agents / MCP.
"""

from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

PHI = (1.0 + math.sqrt(5.0)) / 2.0

WOOD_DRAGON_DAYS = 0.91
DEEP_SPACE_DAYS = 16.35
STATUS_PATH = Path("symplectic_status.json")


def phase_in_cycle(period_days: float, now: Optional[datetime] = None) -> float:
    """Fractional phase [0, 1) of the current UTC day-number in the period."""
    now = now or datetime.now(timezone.utc)
    # days since Unix epoch (float)
    epoch_days = now.timestamp() / 86400.0
    return (epoch_days % period_days) / period_days


def run_wood_dragon_technique(status_path: Path = STATUS_PATH) -> Dict[str, Any]:
    """
    Clarity pass: load symplectic status if available, attach cadence phases.
    Does not require a live cluster; pure file + arithmetic.
    """
    status: Optional[Dict[str, Any]] = None
    if status_path.is_file():
        try:
            status = json.loads(status_path.read_text(encoding="utf-8"))
        except Exception as exc:
            status = {"error": str(exc)}

    now = datetime.now(timezone.utc)
    report: Dict[str, Any] = {
        "technique": "run_wood_dragon_technique",
        "timestamp": now.isoformat(),
        "rhythms": {
            "wood_dragon_days": WOOD_DRAGON_DAYS,
            "deep_space_days": DEEP_SPACE_DAYS,
            "wood_dragon_phase": round(phase_in_cycle(WOOD_DRAGON_DAYS, now), 6),
            "deep_space_phase": round(phase_in_cycle(DEEP_SPACE_DAYS, now), 6),
            "phi": PHI,
        },
        "status_present": status is not None and "error" not in (status or {}),
        "coherence": (status or {}).get("coherence"),
        "seal": "∀∞φ² · WOOD_DRAGON · SEALED",
    }
    if status is not None:
        report["status_name"] = status.get("name")
        report["status_version"] = status.get("version")
    return report


def main() -> None:
    report = run_wood_dragon_technique()
    print(json.dumps(report, indent=2, ensure_ascii=False))
    print(
        f"wood_dragon_phase={report['rhythms']['wood_dragon_phase']} "
        f"deep_space_phase={report['rhythms']['deep_space_phase']}"
    )


if __name__ == "__main__":
    main()
