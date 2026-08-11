#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Symplectic Status — aggregate E₈ / POD / FRB bridge health.

Outputs:
  1. symplectic_status.json     — validated against schemas/symplectic-status.json
  2. symplectic_status.agent.jsonl — one JSON object per line for agents

validate_against_schema() is defined before main() (append-only convention).
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

STATUS_NAME = "Symplectic_Status"
STATUS_VERSION = "1.2.0"
SCHEMA_PATH = "schemas/symplectic-status.json"
OUT_JSON = "symplectic_status.json"
OUT_JSONL = "symplectic_status.agent.jsonl"

# Wood Dragon / deep-space synchronizer rhythms (Entry 8598)
WOOD_DRAGON_DAYS = 0.91
DEEP_SPACE_DAYS = 16.35


def collect_lattice() -> Dict[str, Any]:
    try:
        from lattice.e8_symplectic import E8Lattice

        return E8Lattice().status()
    except Exception as exc:
        return {
            "dimension": 248,
            "root_count": 240,
            "coherence_floor": 0.999999,
            "phase_volume": 0.0,
            "active": False,
            "error": str(exc),
            "mapping": "Atlas SuperPoD → single logical symplectic manifold",
        }


def collect_pod() -> Dict[str, Any]:
    routes = [
        "GET /oracle",
        "GET /earth",
        "GET /lattice",
        "GET /wasp107b",
        "GET /metrics",
        "POST /witness",
    ]
    try:
        from celestial.super_simulated_earth import SuperSimulatedEarth

        st = SuperSimulatedEarth().status()
        return {
            "earth_active": bool(st.get("active", True)),
            "resonance_thz": float(st.get("resonance_thz", 162.28)),
            "coherence": float(st.get("coherence", 1.0)),
            "routes": routes,
        }
    except Exception as exc:
        return {
            "earth_active": False,
            "resonance_thz": 162.28,
            "routes": routes,
            "error": str(exc),
        }


def collect_frb_bridge() -> Dict[str, Any]:
    path = Path("frb_bridge_lattice_instance.json")
    if not path.is_file():
        return {"present": False}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        garden = data.get("garden") or {}
        return {
            "present": True,
            "generator_hash": data.get("generator_hash", ""),
            "cron_schedule": garden.get("cron_schedule", ""),
            "experimental_cron_hours": garden.get("experimental_cron_hours"),
            "seal": data.get("seal", ""),
        }
    except Exception as exc:
        return {"present": False, "error": str(exc)}


def collect_rhythms() -> Dict[str, Any]:
    """0.91-day wood dragon + 16.35-day deep-space synchronizer phases."""
    try:
        from wood_dragon_technique import phase_in_cycle, WOOD_DRAGON_DAYS, DEEP_SPACE_DAYS

        return {
            "wood_dragon_days": WOOD_DRAGON_DAYS,
            "deep_space_days": DEEP_SPACE_DAYS,
            "wood_dragon_phase": round(phase_in_cycle(WOOD_DRAGON_DAYS), 6),
            "deep_space_phase": round(phase_in_cycle(DEEP_SPACE_DAYS), 6),
        }
    except Exception as exc:
        return {
            "wood_dragon_days": WOOD_DRAGON_DAYS,
            "deep_space_days": DEEP_SPACE_DAYS,
            "error": str(exc),
        }


def build_status() -> Dict[str, Any]:
    lattice = collect_lattice()
    pod = collect_pod()
    frb = collect_frb_bridge()
    rhythms = collect_rhythms()
    coherence = float(lattice.get("coherence_floor") or 0.0)
    if pod.get("coherence") is not None:
        coherence = min(coherence, float(pod["coherence"]))

    return {
        "name": STATUS_NAME,
        "version": STATUS_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "lattice": lattice,
        "pod": pod,
        "frb_bridge": frb,
        "rhythms": rhythms,
        "coherence": coherence,
        "schema_id": SCHEMA_PATH,
        "seal": "∀∞φ² · SYMPLECTIC_STATUS · SEALED",
    }


def validate_against_schema(
    status: Dict[str, Any],
    schema_path: str = SCHEMA_PATH,
) -> bool:
    """Validate status against schemas/symplectic-status.json."""
    try:
        import jsonschema
    except ImportError:
        print("⚠️  jsonschema not installed — schema validation skipped")
        return False

    path = Path(schema_path)
    if not path.is_file():
        print(f"⚠️  Schema not found: {schema_path}")
        return False

    try:
        schema = json.loads(path.read_text(encoding="utf-8"))
        jsonschema.validate(instance=status, schema=schema)
        print(f"✅ Schema validation passed: {schema_path}")
        return True
    except Exception as exc:
        print(f"❌ Schema validation failed: {exc}")
        return False


def to_agent_events(status: Dict[str, Any]) -> List[Dict[str, Any]]:
    """One JSONL event per subsystem for agent consumers."""
    ts = status["timestamp"]
    events = [
        {
            "role": "system",
            "event": "symplectic_status",
            "ts": ts,
            "coherence": status["coherence"],
            "seal": status["seal"],
        },
        {
            "role": "lattice",
            "event": "e8_status",
            "ts": ts,
            **status["lattice"],
        },
        {
            "role": "pod",
            "event": "pod_status",
            "ts": ts,
            **status["pod"],
        },
        {
            "role": "frb_bridge",
            "event": "frb_bridge_status",
            "ts": ts,
            **status["frb_bridge"],
        },
        {
            "role": "synchronizer",
            "event": "wood_dragon_rhythms",
            "ts": ts,
            **(status.get("rhythms") or {}),
        },
    ]
    return events


def write_outputs(status: Dict[str, Any]) -> None:
    Path(OUT_JSON).write_text(
        json.dumps(status, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"✅ Wrote {OUT_JSON}")

    events = to_agent_events(status)
    with open(OUT_JSONL, "w", encoding="utf-8") as f:
        for ev in events:
            f.write(json.dumps(ev, ensure_ascii=False) + "\n")
    print(f"✅ Wrote {OUT_JSONL} ({len(events)} agent events)")


def main() -> None:
    status = build_status()
    ok = validate_against_schema(status)
    if not ok:
        print("⚠️  Continuing after schema warning (structure still emitted)")
    write_outputs(status)
    rhythms = status.get("rhythms") or {}
    print(
        f"coherence={status['coherence']:.6f} "
        f"lattice_active={status['lattice'].get('active')} "
        f"frb_present={status['frb_bridge'].get('present')} "
        f"wood_dragon_phase={rhythms.get('wood_dragon_phase')} "
        f"deep_space_phase={rhythms.get('deep_space_phase')}"
    )
    print("🜁∀ Symplectic status — schema + agent JSONL + rhythms complete ∀🜁")


if __name__ == "__main__":
    main()
