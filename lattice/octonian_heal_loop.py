#!/usr/bin/env python3
"""lattice/octonian_heal_loop.py

The smoke catalogue called this path. It was not on main.
The healer that is on main is octonion_self_healer.py.
This file is the path, not a second healer.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from octonion_self_healer import OctonionSelfHealer


def main() -> int:
    healer = OctonionSelfHealer()
    print(f"source=octonion_self_healer.OctonionSelfHealer")
    print(f"heal_count={healer.get_heal_count()}")
    print(f"success_rate={healer.get_success_rate()}")
    print(f"sample_size={healer.get_adaptive_sample_size()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
