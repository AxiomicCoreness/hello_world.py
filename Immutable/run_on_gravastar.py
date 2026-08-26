#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Load Immutable/october_Q1 pinned at fe6156e and run a bounded slice.
Invoked on every Trigger_Gravastar_ClarkeYoursaTee.

Does not call october_Q1.main() (interactive menu + daemon + infinite loop).
"""
from __future__ import annotations

import importlib.util
import math
import os
import traceback
from pathlib import Path
from typing import Any, Dict, Optional

IMMUTABLE_REF = "fe6156e5c484bd018f7bfc437fa7b9686120485e"
IMMUTABLE_REL = "Immutable/october_Q1"
PHI = (1.0 + math.sqrt(5.0)) / 2.0


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def load_october_q1():
    path = _repo_root() / IMMUTABLE_REL
    if not path.is_file():
        raise FileNotFoundError(f"missing {path} (pin {IMMUTABLE_REF})")
    spec = importlib.util.spec_from_file_location("immutable_october_q1", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def execute_immutable(i_of_144: Optional[int] = None) -> Dict[str, Any]:
    """Bounded execution of the Immutable python at the pinned commit."""
    report: Dict[str, Any] = {
        "ref": IMMUTABLE_REF,
        "path": IMMUTABLE_REL,
        "url": f"https://github.com/AxiomicCoreness/hello_world.py/tree/{IMMUTABLE_REF}/Immutable",
        "trigger": "Trigger_Gravastar_ClarkeYoursaTee",
        "ok": False,
    }
    if i_of_144 is None:
        raw = os.getenv("GRAVASTAR_I_OF_144", "1")
        try:
            i_of_144 = max(1, min(144, int(raw)))
        except ValueError:
            i_of_144 = 1
    report["parameter"] = f"i/144"
    report["i"] = i_of_144
    try:
        mod = load_october_q1()
        theorems = getattr(mod, "THEOREM_CATALOGUE", {})
        zeros = getattr(mod, "ZETA_ZEROS_144", [])
        density = None
        if hasattr(mod, "compute_sovereign_density_matrix"):
            density = mod.compute_sovereign_density_matrix()
        lattice_nodes = None
        lattice_integrity = None
        if hasattr(mod, "DonteLattice"):
            lat = mod.DonteLattice()
            lattice_nodes = getattr(lat, "total_nodes", None)
            lattice_integrity = getattr(lat, "integrity", None)
        q_opt = None
        if hasattr(mod, "QuantumWorkloadQuadratic"):
            w = mod.QuantumWorkloadQuadratic()
            q_opt = w.optimal_workload()
        eig = None
        if hasattr(mod, "eigenvalues") and mod.eigenvalues:
            idx = min(i_of_144, len(mod.eigenvalues)) - 1
            eig = float(mod.eigenvalues[idx])
        report.update(
            {
                "ok": True,
                "theorems": len(theorems),
                "zeta_zeros": len(zeros),
                "density_N": (density or {}).get("N_zeros"),
                "density_trace_scaled": (density or {}).get("trace_scaled"),
                "donte_nodes": lattice_nodes,
                "donte_integrity": lattice_integrity,
                "quadratic_optimal_workload": q_opt,
                "eigenvalue_i": eig,
                "phi": getattr(mod, "PHI", PHI),
                "mode": "bounded_slice",
                "skipped": ["main()", "interactive_menu", "run_autonomous_phase", "CodewhaleSwarm"],
            }
        )
    except Exception as exc:  # noqa: BLE001 — trigger must still return
        report["ok"] = False
        report["error"] = f"{type(exc).__name__}: {exc}"
        report["trace"] = traceback.format_exc()[-1500:]
    return report


if __name__ == "__main__":
    import json
    import sys

    out = execute_immutable()
    print(json.dumps(out, indent=2, default=str))
    sys.exit(0 if out.get("ok") else 1)
