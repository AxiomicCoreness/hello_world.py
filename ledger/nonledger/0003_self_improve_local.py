#!/usr/bin/env python3
"""Nameplate self-check. Lists this tree. Does not read the engine repo."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BOUND = ("scripts", "docs", ".devcontainer", "router", "static")


def main() -> int:
    counts = {}
    for name in BOUND:
        path = ROOT / name
        counts[name] = len(list(path.iterdir())) if path.is_dir() else 0
    print(json.dumps({"repo": "ClarkeYoursaTee", "counts": counts, "ledger_written": False}, indent=2))
    return 0 if all(counts.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
