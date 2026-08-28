"""Poincare dodecahedron to Pisano period. Geometry + named cutoffs."""
from __future__ import annotations
import json, math
from pathlib import Path
from typing import Any, Dict, List
PHI = (1.0 + math.sqrt(5.0)) / 2.0
PHASE_LOCK_DEG = 202.6
PSI_DEG = math.degrees(math.pi / PHI)
PISANO_10 = 60
BINARY_ICOSAHEDRAL_ORDER = 120
FLUX_CUTOFF = PHI ** -12
NDJSON = Path(__file__).resolve().parents[1] / "poincare_dodecahedral_state.ndjson"

def order_config() -> Dict[str, Any]:
    n = BINARY_ICOSAHEDRAL_ORDER
    p10 = PISANO_10
    return {
        "pisano_divides_order": n % p10 == 0,
        "quotient_2I_over_pisano": n // p10,
        "inverse_of_order": 1.0 / n,
        "inverse_of_order_in_Z": False,
        "circle_pi_divides_order_in_Z": False,
        "order_over_circle_pi": n / math.pi,
        "circle_pi_over_order": math.pi / n,
    }

def math_form() -> Dict[str, Any]:
    return {
        "phi": PHI,
        "psi_deg": PSI_DEG,
        "phase_lock_deg": PHASE_LOCK_DEG,
        "pisano_pi_10": PISANO_10,
        "binary_icosahedral_order": BINARY_ICOSAHEDRAL_ORDER,
        "flux_cutoff_phi_neg_12": FLUX_CUTOFF,
        "order": order_config(),
    }

def default_state() -> Dict[str, Any]:
    return {
        "version": "9100",
        "geometry": {"type": "Poincare dodecahedral", "fundamental_group": "binary icosahedral", "volume_scaling": "phi^-12"},
        "invariants": {"phi": PHI, "phase_lock": PHASE_LOCK_DEG, "pisano_10": PISANO_10, "flux_cutoff": FLUX_CUTOFF, "witness": "9100"},
        "attached_nodes": ["frb_name_seal", "lattice_48", "canonical_json"],
        "seal": "POINCARE_PISANO_9100",
    }

def write_ndjson(path: Path = NDJSON) -> Path:
    path.write_text(json.dumps(default_state(), sort_keys=True) + "\n", encoding="utf-8")
    return path

def suite_geometry(strict: bool = False) -> Dict[str, Any]:
    if not NDJSON.exists():
        write_ndjson(NDJSON)
    lines = [ln.strip() for ln in NDJSON.read_text().splitlines() if ln.strip()]
    if not lines:
        return {"name": "geometry", "passed": False, "message": "No entries in ndJSON"}
    errors: List[str] = []
    for i, line in enumerate(lines):
        try:
            state = json.loads(line)
            inv, geo = state["invariants"], state["geometry"]
            assert abs(float(inv["phi"]) - PHI) < 1e-6
            assert abs(float(inv["phase_lock"]) - PHASE_LOCK_DEG) < 0.1
            assert geo.get("fundamental_group") == "binary icosahedral"
        except Exception as exc:
            errors.append(f"line {i}: {exc}")
    if errors:
        return {"name": "geometry", "passed": False, "message": "; ".join(errors)}
    return {"name": "geometry", "passed": True, "message": f"All Poincare states valid ({len(lines)} line(s))", "math": math_form()}

if __name__ == "__main__":
    r = suite_geometry()
    print(r["passed"], r["message"])
    raise SystemExit(0 if r["passed"] else 1)
