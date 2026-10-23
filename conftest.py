"""Repo-root pytest bootstrap: put the repository root on ``sys.path``.

Ensures imports like ``scripts.recalc_optics`` resolve when collecting deep
tests (e.g. ``skills/lambda0_provenance/evals/test_recalc.py``).
"""
from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = str(Path(__file__).resolve().parent)
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)
