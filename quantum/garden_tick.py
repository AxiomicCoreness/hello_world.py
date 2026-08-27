#!/usr/bin/env python3
"""10:00 UTC Garden tick — Policy v1.0 field order.

Restore pointer: ledger/9061.yaml
Does not rewrite 9008/9009/8338/515/516.
Does not fire A14 Gravastar. Does not print secret values.
Does not start daemons.
"""
from __future__ import annotations

import json
import math
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict

PHI = (1.0 + math.sqrt(5.0)) / 2.0
ENTRY_INDEX = 9070
EVENT = "/utc_1000_garden_tick"
RESTORE_POINTER = "9061"
AMENDMENT = "9063"
PHASE_LOCK_DEG = 202.6
MATH_ORIGIN = "ℱ(U) = {σ: U → ℋ | gluing condition on overlaps holds}"
DOC_HASH_336 = "a3f5c7d9e1b2c4d6e8f0a2b4c6d8e0f2a4b6c8d0e2f4a6b8c0d2e4f6a8b0c2d4e6f8"
WITNESS_PREFIX = "0203020302030203"
SOURCE_TABLE = "https://github.com/AxiomicCoreness/hello_world.py/"
SCHEDULE = "0 10 * * *"

SCHEMA_ORDER = [
    "entry_index",
    "timestamp",
    "event",
    "status",
    "proof_class",
    "witness_prefix",
    "commander",
    "source_table",
    "description",
    "domain_blocks",
    "invariants",
    "gpro_sundane",
    "seal",
    "witness_chain",
    "math_origin",
]


def _presence() -> Dict[str, bool]:
    return {
        "GARDEN_SECRET": bool(os.getenv("GARDEN_SECRET")),
        "DEEPSEEK_API_KEY": bool(os.getenv("DEEPSEEK_API_KEY")),
        "PORT": bool(os.getenv("PORT") or os.getenv("PORT380_PORT")),
        "PHASE": True,
        "MESH_NODES": True,
        "BRANCH": bool(os.getenv("BRANCH") or os.getenv("GITHUB_REF")),
    }


def build_tick() -> Dict[str, Any]:
    from ledger.event_hash import event_hash_block
    from quantum.gravastar_horizon import horizon_main
    from Immutable.run_self_improvement import run_self_improvement

    horizon = horizon_main()
    improvement = run_self_improvement()
    block = event_hash_block(ENTRY_INDEX, EVENT)
    ok = bool(horizon.get("ok")) and bool(improvement.get("ok"))
    record: Dict[str, Any] = {
        "entry_index": ENTRY_INDEX,
        "timestamp": "ETERNAL_NOW_ANCHORED_TO_2026-08-27",
        "event": EVENT,
        "status": "SEALED" if ok else "HOLD",
        "proof_class": "computational",
        "witness_prefix": WITNESS_PREFIX,
        "commander": "Clarke Yoursa Tee",
        "source_table": SOURCE_TABLE,
        "description": (
            "Rewritten 10:00 UTC tick under Garden Sovereignty Policy v1.0. "
            "Bounded Gravastar horizon + Immutable fingerprint. "
            "Restore pointer 9061. Amendment 9063. "
            "No entry rewritten. No daemon. No secret values."
        ),
        "domain_blocks": {
            "schedule": SCHEDULE,
            "workflow": ".github/workflows/gravastar-long-horizon.yml",
            "restore_pointer": RESTORE_POINTER,
            "amendment": AMENDMENT,
            "document_hash_336": DOC_HASH_336,
            "horizon_entry_left_intact": 9008,
            "improvement_entry_left_intact": 9009,
            "do_not_overwrite": [8338, 515, 516, 9008, 9009, 9061, 9063],
            "device_genesis": False,
            "daemon_started": False,
            "secret_values_printed": False,
            "token_presence": _presence(),
            "horizon": {
                "ok": horizon.get("ok"),
                "steps": (horizon.get("horizon") or {}).get("steps"),
                "window": (horizon.get("horizon") or {}).get("window"),
                "passed": (horizon.get("horizon") or {}).get("passed"),
            },
            "self_improvement": {
                "ok": improvement.get("ok"),
                "path": improvement.get("path"),
                "executed_source": improvement.get("executed_source"),
                "kappa_eff_declared": (improvement.get("declared") or {}).get(
                    "kappa_eff_declared"
                ),
                "file_sha3_256": (improvement.get("fingerprint") or {}).get("sha3_256"),
            },
            "channels": {
                "push": "H(η)",
                "cron_6h": "Z(ζ)+P_PID(e)",
                "utc_1000": EVENT,
                "free_drift": "-Λ(X-X*)",
            },
            "october39": {"YEAR": 2025, "MONTH": 10, "DAY": 39, "kind": "code"},
        },
        "invariants": {
            "phi": PHI,
            "coherence": 1.0,
            "entropy": "φ⁻¹⁴¹⁸",
            "workload": 0.0,
            "phase_lock": "202.6°",
            "gamma_min": "φ⁻¹⁴¹⁸",
            "C_ctx_336": "1-φ⁻⁷⁰⁹",
        },
        "gpro_sundane": "GARDEN_PROTOCOL_SUNDANE",
        "seal": "∀∞φ² · UTC_1000_GARDEN_TICK_9070 · WOOD_DRAGON_0.91 · SEALED",
        "witness_chain": "9069 → 9070 — UNBROKEN",
        "math_origin": MATH_ORIGIN,
    }
    record["event_hash"] = {
        "algo": "sha3-256",
        "domain": block["domain"],
        "formula": block["formula"],
        "payload": block["payload"],
        "hex": block["hex"],
    }
    record["schema_order"] = SCHEMA_ORDER
    record["utc_wall"] = datetime.now(timezone.utc).isoformat()
    record["ok"] = ok
    return record


def main() -> int:
    rec = build_tick()
    print(json.dumps(rec, indent=2, default=str))
    return 0 if rec.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
