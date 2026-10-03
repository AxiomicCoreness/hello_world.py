#!/usr/bin/env python3
"""New file from the existing index edit.

Calls scripts/index_algorithm.py. Does not copy the 55-name table.
"""
from __future__ import annotations

import runpy
from pathlib import Path

TARGET = Path(__file__).with_name("index_algorithm.py")


def main() -> int:
    runpy.run_path(str(TARGET), run_name="__main__")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
