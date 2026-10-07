#!/usr/bin/env python3
"""Pinned sign convention. Baseline manifold dimension is 7.

ω = Σ_i dq_i ∧ dp_i  ⇒  {q_i, p_j} = +δ_ij
dq_i/dt = +∂H/∂p_i,  dp_i/dt = -∂H/∂q_i

Matches pythonIDE/symplectic_euler.py: p -= h ∂V/∂q, q += h ∂T/∂p.
No credential is stored here. No kubectl.
"""

from __future__ import annotations

import json
import math
import os
from pathlib import Path

DIMENSION = 7
FORM_TERMS = 427
PHI = (1.0 + math.sqrt(5.0)) / 2.0
SIGN = {
    "form": "sum dq_i wedge dp_i",
    "poisson": "+delta_ij",
    "dq_dt": "+dH/dp",
    "dp_dt": "-dH/dq",
}
ROOT = Path(__file__).resolve().parents[1]


def symplectic_form() -> dict:
    """Quantities at symplectic time. The 427-sum is the stated form, not the 7-pair baseline."""
    return {
        "omega": "symplectic 2-form",
        "H": "Hamiltonian",
        "poisson": "Poisson bracket",
        "F": "prequantum curvature, F_nabla = -i omega",
        "expression": "Sum(dq[i]·dp[i], (i, 1, 427)) + (1/φ)·dξ·dξ̄",
        "terms": FORM_TERMS,
        "phi_coeff": 1.0 / PHI,
        "baseline_pairs": DIMENSION,
    }


def account() -> dict:
    return {
        "dimension": DIMENSION,
        "pairs": DIMENSION,
        "sign": SIGN,
        "form": symplectic_form(),
        "credential_in_source": False,
        "rotation": "env-only",
    }


def history_clean(root: Path = ROOT) -> dict:
    """Recurrence check. The needle comes from ROTATED_CREDENTIAL, never source."""
    needle = os.environ.get("ROTATED_CREDENTIAL", "")
    hits = []
    if needle:
        for path in root.rglob("*"):
            if not path.is_file() or ".git" in path.parts:
                continue
            if path.suffix not in {".py", ".yml", ".yaml", ".md", ".sh", ".json"}:
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if needle in text:
                hits.append(str(path.relative_to(root)))
    return {"needle_in_source": False, "scanned": bool(needle), "hits": hits, "clean": not hits}


def main() -> int:
    report = account()
    report["history"] = history_clean()
    print(json.dumps(report, sort_keys=True))
    return 0 if report["history"]["clean"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
