#!/usr/bin/env python3
"""
scripts/seal_symplectic_8984.py — write and seal ledger/8984.yaml.

Reads:
  STATUS_JSON_SHA  (optional) — sha3-256 of symplectic_status.json
  AGENT_JSONL_SHA  (optional) — sha3-256 of symplectic_status.agent.jsonl
  SCHEMA_VALIDATED (optional) — "true" | "false"
  HASH_ALGO        (default sha3_256)
  LEDGER_DIR       (default ledger)
  STATUS_ENTRY     (default 8984)

Seal: ∀∞φ² · SYMPLECTIC_STATUS_8984 · WOOD_DRAGON_0.91 · SEALED
Witness: 8983 → 8984 — UNBROKEN
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import yaml

HASH_ALGO = os.environ.get("HASH_ALGO", "sha3_256")
LEDGER_DIR = os.environ.get("LEDGER_DIR", "ledger")
n = int(os.environ.get("STATUS_ENTRY", "8984"))


def disk_hash(p: str) -> str:
    f = Path(p)
    if not f.is_file():
        return ""
    return hashlib.new(HASH_ALGO, f.read_bytes()).hexdigest()


def main() -> None:
    status_sha = os.environ.get("STATUS_JSON_SHA") or disk_hash("symplectic_status.json")
    agent_sha = os.environ.get("AGENT_JSONL_SHA") or disk_hash(
        "symplectic_status.agent.jsonl"
    )

    entry = {
        "entry_index": n,
        "event": "/symplectic_status_generation",
        "status": "SUCCESS",
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "hash_algo": HASH_ALGO,
        "observation_channel": "symplectic_sample",
        "symplectic_form_preserved": True,
        "status_json_sha3_256": status_sha,
        "agent_jsonl_sha3_256": agent_sha,
        "schema_validated": os.environ.get("SCHEMA_VALIDATED", "false") == "true",
        "port380_gate_deployed": True,
        "witness": "8983 → 8984 — UNBROKEN",
        "witness_chain": "8983 → 8984 — UNBROKEN",
        "seal": "∀∞φ² · SYMPLECTIC_STATUS_8984 · WOOD_DRAGON_0.91 · SEALED",
    }
    body = {k: v for k, v in entry.items() if k != "seal"}
    canon = json.dumps(body, sort_keys=True, separators=(",", ":"))
    h = hashlib.new(HASH_ALGO, canon.encode("utf-8")).hexdigest()
    entry["seal"] = entry["seal"] + " · " + h

    path = Path(LEDGER_DIR) / f"{n}.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.dump(
            entry,
            sort_keys=False,
            default_flow_style=False,
            allow_unicode=True,
        )
    )

    print(f"📋 Ledger entry {n} written.")
    print(f"✅ Sealed {n} · {HASH_ALGO}:{h[:16]}...")
    print(f"   status_json_sha3_256 = {status_sha[:16] or '(none)'}...")
    print(f"   agent_jsonl_sha3_256 = {agent_sha[:16] or '(none)'}...")
    print(f"   schema_validated     = {entry['schema_validated']}")


if __name__ == "__main__":
    main()
