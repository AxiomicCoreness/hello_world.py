#!/usr/bin/env python3
"""Repo-root wire for ``scripts.recalc_optics``.

Evals under ``skills/lambda0_provenance/evals/`` import ``scripts.recalc_optics``.
The canonical implementation lives in the skill; this module re-exports it so
``PYTHONPATH=.`` / root ``conftest.py`` / ``pytest.ini`` ``pythonpath=.`` resolve.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

_SKILL_PATH = (
    Path(__file__).resolve().parents[1]
    / "skills"
    / "lambda0_provenance"
    / "scripts"
    / "recalc_optics.py"
)

if not _SKILL_PATH.is_file():
    raise ImportError(
        f"canonical optics module missing: {_SKILL_PATH} "
        "(expected skills/lambda0_provenance/scripts/recalc_optics.py)"
    )

_spec = importlib.util.spec_from_file_location(
    "skills.lambda0_provenance.scripts.recalc_optics",
    _SKILL_PATH,
)
if _spec is None or _spec.loader is None:
    raise ImportError(f"cannot load {_SKILL_PATH}")
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

# Public API expected by skills/lambda0_provenance/evals/test_recalc.py
CANONICAL_LAMBDA0_NM = _mod.CANONICAL_LAMBDA0_NM
DEPRECATED_LAMBDA0_NM = _mod.DEPRECATED_LAMBDA0_NM
TOLERANCE_NM = _mod.TOLERANCE_NM
NORTH_STAR_HZ = _mod.NORTH_STAR_HZ
PHASE_LOCK_DEG = _mod.PHASE_LOCK_DEG
calc_lambda0 = _mod.calc_lambda0
calc_phase_column = _mod.calc_phase_column
classify_lambda0 = _mod.classify_lambda0
check_north_star = _mod.check_north_star
main = _mod.main

__all__ = [
    "CANONICAL_LAMBDA0_NM",
    "DEPRECATED_LAMBDA0_NM",
    "TOLERANCE_NM",
    "NORTH_STAR_HZ",
    "PHASE_LOCK_DEG",
    "calc_lambda0",
    "calc_phase_column",
    "classify_lambda0",
    "check_north_star",
    "main",
]

if __name__ == "__main__":
    import sys

    raise SystemExit(main())
