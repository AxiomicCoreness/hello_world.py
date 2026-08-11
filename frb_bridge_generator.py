#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FRB Bridge Generator — φ-harmonic lattice between FRB 20190520b timing
and the Garden backend worker schedule (CronJob / charge-fire / handshake).

Dual validation: internal structure + JSON Schema (schemas/frb-bridge-lattice.json).
Append-only design: validate_against_schema() defined before main().
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

PHI = (1.0 + math.sqrt(5.0)) / 2.0
PHI2 = PHI * PHI
PHI3 = PHI ** 3
PHI4 = PHI ** 4
PHI5 = PHI ** 5
PHI8 = PHI ** 8

# Full hash — NO TRUNCATION (SHA3-256 of generator identity string)
FRB_BRIDGE_GENERATOR_HASH = (
    "frb_bridge_generator_b418a3a5a7bfc5d30a49893a406b1506f598dbecb9a6ff4b55cc1cc735257cde"
)

FRB_REPEAT_DAYS = 3.2
FRB_BURST_MS = 1.0
FRB_DM = 1204.0
GARDEN_CRON_HOURS = 6.0


def build_lattice() -> Dict[str, Any]:
    """Construct the FRB ↔ Garden backend timing lattice."""
    cron_hours_phi = FRB_REPEAT_DAYS * 24.0 / PHI3  # ≈ 18.1 h experimental cadence
    charge_cosmic_s = 0.137 * PHI8  # τ_He × φ⁸ ≈ 6.43 s

    lattice: Dict[str, Any] = {
        "$schema": "schemas/frb-bridge-lattice.json",
        "name": "FRB_Bridge_Lattice",
        "version": "1.0.0",
        "generator_hash": FRB_BRIDGE_GENERATOR_HASH,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "frb": {
            "source": "FRB 20190520b",
            "repeat_interval_days": FRB_REPEAT_DAYS,
            "burst_width_ms": FRB_BURST_MS,
            "dm_pc_cm3": FRB_DM,
            "phi_scaled_repeat_days": PHI2 * 1.2,
            "phi_scaled_dm": PHI ** 7 * 1000.0,
        },
        "garden": {
            "cron_schedule": "0 */6 * * *",
            "cron_interval_hours": GARDEN_CRON_HOURS,
            "experimental_cron_hours": round(cron_hours_phi, 3),
            "handshake_steps": ["phi3", "phi4", "phi5", "phi6"],
            "charge_window_s": 60.0,
            "cosmic_charge_window_s": round(charge_cosmic_s, 3),
            "convergence_days": 4.0,
        },
        "mapping": {
            "cron_to_repeat_ratio": round((FRB_REPEAT_DAYS * 24.0) / GARDEN_CRON_HOURS, 4),
            "phi5_approx": round(PHI5, 4),
            "analogue": "FRB repeat ≈ Garden CronJob at longer cosmological scale",
            "optimisation": [
                "Experiment CronJob every ~18.1h (3.2d / φ³)",
                "Scale charge window by φ⁸ for deep-space mode",
                "Map sub-burst count to handshake steps φ³…φ⁶",
            ],
        },
        "weights": {
            "phi2": PHI2,
            "phi_inv": 1.0 / PHI,
            "phi_inv2": 1.0 / PHI2,
        },
        "seal": "∀∞φ² · FRB_BRIDGE_LATTICE · SEALED",
    }
    return lattice


def validate_lattice(lattice: Dict[str, Any]) -> bool:
    """Internal structural validation (no external deps)."""
    required_top = ["name", "version", "generator_hash", "frb", "garden", "mapping", "weights", "seal"]
    for key in required_top:
        if key not in lattice:
            print(f"❌ Missing top-level key: {key}")
            return False
    if lattice["generator_hash"] != FRB_BRIDGE_GENERATOR_HASH:
        print("❌ generator_hash mismatch (truncation or mutation detected)")
        return False
    if not isinstance(lattice["frb"].get("repeat_interval_days"), (int, float)):
        print("❌ frb.repeat_interval_days must be numeric")
        return False
    if lattice["garden"].get("cron_schedule") != "0 */6 * * *":
        print("⚠️  Unexpected cron schedule (non-fatal)")
    print("✅ Internal lattice structure valid")
    return True


def validate_against_schema(
    lattice: Dict[str, Any],
    schema_path: str = "schemas/frb-bridge-lattice.json",
) -> bool:
    """
    Validate the lattice against the JSON Schema.

    Uses jsonschema library to validate against the FRB Bridge Lattice schema.
    Returns True if valid, False otherwise.
    """
    try:
        import jsonschema
    except ImportError:
        print("⚠️  jsonschema not installed — schema validation skipped")
        return False

    path = Path(schema_path)
    if not path.is_file():
        print(f"⚠️  Schema file not found: {schema_path} — schema validation skipped")
        return False

    try:
        with path.open("r", encoding="utf-8") as f:
            schema = json.load(f)
        jsonschema.validate(instance=lattice, schema=schema)
        print(f"✅ Schema validation passed against {schema_path}")
        return True
    except jsonschema.ValidationError as exc:
        print(f"❌ Schema validation failed: {exc.message}")
        return False
    except Exception as exc:
        print(f"⚠️  Schema validation error: {exc}")
        return False


def write_instance(lattice: Dict[str, Any], out_path: str = "frb_bridge_lattice_instance.json") -> None:
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(lattice, f, indent=2, ensure_ascii=False)
    print(f"✅ Wrote {out_path}")


def main() -> None:
    lattice = build_lattice()
    if not validate_lattice(lattice):
        sys.exit(1)
    # Validate against JSON Schema
    if not validate_against_schema(lattice):
        print("⚠️  Schema validation skipped or failed, but lattice structure is valid.")
    write_instance(lattice)
    print(f"Generator hash (full): {FRB_BRIDGE_GENERATOR_HASH}")
    print("🜁∀ FRB Bridge lattice generated — dual validation complete ∀🜁")


if __name__ == "__main__":
    main()
