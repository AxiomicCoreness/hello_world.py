#!/usr/bin/env python3
"""Index script for the parity algorithm.

Same formula as scripts/traffic_cop.py and workflow-parity.yml:
    slot = (day * 1440 + hour * 60 + minute) // 15 % 55

Names are imported from the sibling file. This script does not dispatch.
"""
from __future__ import annotations

import importlib.util
from datetime import datetime, timezone
from pathlib import Path

_SRC = Path(__file__).with_name("traffic_cop.py")
_spec = importlib.util.spec_from_file_location("traffic_cop", _SRC)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
FILES = _mod.FILES
N = len(FILES)


def slot_index(day: int, hour: int, minute: int) -> int:
    if not (1 <= day <= 31 and 0 <= hour <= 23 and 0 <= minute <= 59):
        raise ValueError("day, hour, minute out of range")
    return (day * 1440 + hour * 60 + minute) // 15 % N


def slot_name(day: int, hour: int, minute: int) -> str:
    return FILES[slot_index(day, hour, minute)]


def index_now(now: datetime | None = None) -> tuple[int, str]:
    now = now or datetime.now(timezone.utc)
    idx = slot_index(now.day, now.hour, now.minute)
    return idx, FILES[idx]


def main() -> int:
    idx, name = index_now()
    print(f"{idx} {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
