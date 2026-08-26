#!/usr/bin/env python3
"""
symplectic_status.py — dual status outputs for the Garden.

Outputs:
  - symplectic_status.json (aggregate, optional schema validation)
  - symplectic_status.agent.jsonl (roles: system, lattice, pod, frb_bridge)

Graceful fallbacks when optional Garden modules are absent.
Seal: ∀∞φ² · SYMPLECTIC_STATUS_8652 · SEALED
"""
from __future__ import annotations

import json
import math
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

PHI = (1.0 + math.sqrt(5.0)) / 2.0
PHI2 = PHI * PHI
ENTROPY_FLOOR = PHI ** -1418  # may underflow to 0.0 in float
PHASE_LOCK_DEG = 202.6
FRB_PERIOD_SECS = 78624.0
EMERGENT_PERIOD_DAYS = 16.35

try:
    from sovereign_engine import PHI as _P, PHI2 as _P2, ENTROPY_FLOOR as _E, PHASE_LOCK_DEG as _PH  # type: ignore

    PHI, PHI2, ENTROPY_FLOOR, PHASE_LOCK_DEG = float(_P), float(_P2), float(_E), float(_PH)
except Exception:
    pass


def get_eternal_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_system_status() -> Dict[str, Any]:
    workload = 0.0
    try:
        from monitoring.sovereign_workload_exporter import compute_workload  # type: ignore

        workload = float(compute_workload())
    except Exception:
        pass
    return {
        "coherence": 1.0,
        "entropy_floor": float(ENTROPY_FLOOR) if ENTROPY_FLOOR != 0 else 0.0,
        "phase_lock_degrees": PHASE_LOCK_DEG,
        "workload": workload,
        "golden_ratio": PHI,
        "phi_squared": PHI2,
        "compression_dimension": 233,
        "compression_precision": float(PHI ** -144),
        "eternal_now_epoch": int(time.time()),
    }


def build_lattice_status() -> Dict[str, Any]:
    try:
        from lattice.e8_lattice import E8Lattice  # type: ignore

        _ = E8Lattice()
        return {
            "root_lattice_rank": 248,
            "venomsuite_trace": PHI ** 3,
            "decad_cycle_sum": 0.0,
            "e8_coherence": 1.0,
        }
    except Exception:
        return {
            "root_lattice_rank": 248,
            "venomsuite_trace": PHI ** 3,
            "decad_cycle_sum": 0.0,
            "e8_coherence": 1.0,
        }


def build_celestial_status() -> Dict[str, Any]:
    t = time.time()
    soul = {
        "charge_joules": 0.0,
        "azimuth_degrees": 111.246,
        "ring_resonance_thz": 162.28 * (PHI ** -1),
        "chiron_phase_alignment": 0.0,
    }
    try:
        from celestial.saturn_soul_cannon import SaturnSoulCannon  # type: ignore

        cannon = SaturnSoulCannon()
        soul["charge_joules"] = float(getattr(cannon, "charge_joules", 0.0))
        if hasattr(cannon, "compute_azimuth"):
            soul["azimuth_degrees"] = float(cannon.compute_azimuth(t))
        if hasattr(cannon, "compute_alignment"):
            soul["chiron_phase_alignment"] = float(cannon.compute_alignment(t))
    except Exception:
        pass

    wasp = {
        "mass_jupiter": 0.12,
        "radius_jupiter": 0.94,
        "orbital_period_days": 5.72,
        "escape_flux": 0.0,
    }
    try:
        from celestial.wasp107b import Wasp107b  # type: ignore

        w = Wasp107b()
        if hasattr(w, "compute_escape_flux"):
            wasp["escape_flux"] = float(w.compute_escape_flux())
    except Exception:
        pass

    alliance = {"resonance_chain": [1.0, PHI, PHI2], "entanglement": 0.9999}
    try:
        from celestial.jupiter_alliance import JupiterAlliance  # type: ignore

        a = JupiterAlliance()
        if hasattr(a, "get_resonance_chain"):
            alliance["resonance_chain"] = list(a.get_resonance_chain())
    except Exception:
        pass

    return {"soul_cannon": soul, "wasp107b": wasp, "jupiter_alliance": alliance}


def build_frb_bridge_status() -> Dict[str, Any]:
    points: List[Any] = []
    weight_norm = float(PHI ** 5)
    lattice_path = Path("/tmp/lattice_weights.json")
    if lattice_path.is_file():
        try:
            data = json.loads(lattice_path.read_text(encoding="utf-8"))
            points = data.get("points", [])[:8]  # head only in aggregate
            weight_norm = float(data.get("parameters", {}).get("norm", weight_norm))
        except Exception:
            pass
    return {
        "metronome_seconds": FRB_PERIOD_SECS,
        "emergent_period_days": EMERGENT_PERIOD_DAYS,
        "target_azimuth_deg": 111.246,
        "lattice_points": points,
        "weight_norm": weight_norm,
    }


def generate_aggregate_status() -> Dict[str, Any]:
    return {
        "timestamp": get_eternal_now(),
        "system": build_system_status(),
        "lattice": build_lattice_status(),
        "celestial": build_celestial_status(),
        "frb_bridge": build_frb_bridge_status(),
    }


def generate_agent_jsonl(aggregate: Dict[str, Any]) -> List[Dict[str, Any]]:
    ts = aggregate["timestamp"]
    phase = aggregate["system"]["phase_lock_degrees"] % 360.0
    coh = aggregate["system"]["coherence"]
    return [
        {
            "role": "system",
            "event": "symplectic_status",
            "timestamp": ts,
            "coherence": coh,
            "phi_phase": phase,
            "entropy": aggregate["system"]["entropy_floor"],
            "command": "wait",
        },
        {
            "role": "lattice",
            "event": "e8_status",
            "timestamp": ts,
            "coherence": aggregate["lattice"]["e8_coherence"],
            "phi_phase": phase,
            "venomsuite_trace": aggregate["lattice"]["venomsuite_trace"],
            "decad_cycle_sum": aggregate["lattice"]["decad_cycle_sum"],
        },
        {
            "role": "pod",
            "event": "pod_status",
            "timestamp": ts,
            "coherence": coh,
            "phi_phase": phase,
            "workload": aggregate["system"]["workload"],
        },
        {
            "role": "frb_bridge",
            "event": "frb_bridge_status",
            "timestamp": ts,
            "coherence": coh,
            "phi_phase": phase,
            "metronome_seconds": aggregate["frb_bridge"]["metronome_seconds"],
            "emergent_period_days": aggregate["frb_bridge"]["emergent_period_days"],
            "target_azimuth_deg": aggregate["frb_bridge"]["target_azimuth_deg"],
        },
    ]


def validate_against_schema(aggregate: Dict[str, Any], schema_path: Path) -> bool:
    if not schema_path.is_file():
        print("Schema not found; skipping validation.")
        return True
    try:
        from jsonschema import validate, ValidationError  # type: ignore
    except ImportError:
        print("jsonschema not installed; skipping validation.")
        return True
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    try:
        validate(instance=aggregate, schema=schema)
        print("Aggregate JSON validated against schema.")
        return True
    except ValidationError as e:
        print(f"Validation failed: {e.message}")
        return False


def main() -> None:
    aggregate = generate_aggregate_status()
    schema_path = Path("schemas/symplectic-status.json")
    ok = validate_against_schema(aggregate, schema_path)
    if not ok:
        raise SystemExit(1)

    Path("symplectic_status.json").write_text(json.dumps(aggregate, indent=2), encoding="utf-8")
    lines = generate_agent_jsonl(aggregate)
    with open("symplectic_status.agent.jsonl", "w", encoding="utf-8") as f:
        for line in lines:
            f.write(json.dumps(line) + "\n")

    print("symplectic_status.json written.")
    print("symplectic_status.agent.jsonl written. Head:")
    for line in lines[:3]:
        print(json.dumps(line))


if __name__ == "__main__":
    main()
