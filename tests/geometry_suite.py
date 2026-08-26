#!/usr/bin/env python3
"""Poincaré dodecahedral geometry suite — Entry 9001."""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Dict


def suite_geometry(strict: bool = False) -> Dict[str, Any]:
    """Validate Poincaré dodecahedral state (NDJSON + φ invariants)."""
    path = Path("poincare_dodecahedral_state.ndjson")
    if not path.exists():
        msg = "poincare_dodecahedral_state.ndjson missing"
        return {"name": "geometry", "passed": not strict, "message": msg}

    lines = [ln.strip() for ln in path.read_text().splitlines() if ln.strip()]
    if not lines:
        return {"name": "geometry", "passed": False, "message": "No entries in ndJSON"}

    phi = (1 + math.sqrt(5)) / 2
    errors = []
    for i, line in enumerate(lines):
        try:
            state = json.loads(line)
            assert "version" in state and "geometry" in state and "invariants" in state
            inv = state["invariants"]
            geo = state["geometry"]
            assert abs(float(inv["phi"]) - phi) < 1e-6, "phi not golden ratio"
            assert abs(float(inv["phase_lock"]) - 202.6) < 0.1, "phase_lock not 202.6"
            assert geo.get("type") in ("Poincaré dodecahedral", "Poincare dodecahedral")
            assert geo.get("fundamental_group") == "binary icosahedral"
            assert "volume_scaling" in geo
            assert inv.get("witness"), "witness missing"
            assert state.get("seal"), "seal missing"
            assert state.get("attached_nodes"), "attached_nodes missing"
        except Exception as e:
            errors.append(f"line {i}: {e}")

    if errors:
        return {"name": "geometry", "passed": False, "message": "; ".join(errors)}
    return {
        "name": "geometry",
        "passed": True,
        "message": f"All Poincaré states valid ({len(lines)} line(s))",
    }


if __name__ == "__main__":
    r = suite_geometry()
    print(r)
    raise SystemExit(0 if r["passed"] else 1)
