#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unified Garden harness entrypoint — loads suites from harness_core."""
from __future__ import annotations
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
if str(_ROOT / "tests") not in sys.path:
    sys.path.insert(0, str(_ROOT / "tests"))

from harness_core import *  # noqa: F401,F403
from harness_core import main

if __name__ == "__main__":
    main()
