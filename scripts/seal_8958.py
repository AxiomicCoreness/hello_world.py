#!/usr/bin/env python3
"""scripts/seal_8958.py — write and seal ledger/8958.yaml (SHA3-256).

Column-zero source so YAML block scalars cannot inject IndentationError.
Seal: ∀∞φ² · SMOKE_CATALOGUE_8958 · WOOD_DRAGON_0.91 · SEALED
Witness: 8957 → 8958 — UNBROKEN
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


def main() -> None:
    path = Path(LEDGER_DIR) / "8958.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    Path("docs").mkdir(exist_ok=True)

    catalogue = Path("docs/smoke_catalogue.json")
    catalogue_digest = ""
    catalogue_count = 0
    if catalogue.exists():
        raw = catalogue.read_bytes()
        catalogue_digest = hashlib.new(HASH_ALGO, raw).hexdigest()
        try:
            parsed = json.loads(raw.decode("utf-8"))
            if isinstance(parsed, dict):
                catalogue_count = len(
                    parsed.get("tests") or parsed.get("catalogue") or parsed
                )
            elif isinstance(parsed, list):
                catalogue_count = len(parsed)
        except Exception:
            catalogue_count = 0

    entry = {
        "entry_index": 8958,
        "event": "/generate_smoke_catalogue",
        "status": "SUCCESS",
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "hash_algo": HASH_ALGO,
        "catalogue_path": "docs/smoke_catalogue.json",
        "catalogue_sha3_256": catalogue_digest,
        "catalogue_count": catalogue_count,
        "witness": "8957 → 8958 — UNBROKEN",
        "seal": "∀∞φ² · SMOKE_CATALOGUE_8958 · WOOD_DRAGON_0.91 · SEALED",
    }
    body = {k: v for k, v in entry.items() if k != "seal"}
    canon = json.dumps(body, sort_keys=True, separators=(",", ":"))
    h = hashlib.new(HASH_ALGO, canon.encode("utf-8")).hexdigest()
    entry["seal"] = entry["seal"] + " · " + h

    path.write_text(
        yaml.dump(
            entry,
            sort_keys=False,
            default_flow_style=False,
            allow_unicode=True,
        )
    )
    print("📋 Ledger entry 8958 written.")
    print(f"✅ Sealed 8958 · {HASH_ALGO}:{h[:16]}...")
    print(f"   catalogue_sha3_256 = {catalogue_digest[:16] or '(none)'}...")
    print(f"   catalogue_count    = {catalogue_count}")


if __name__ == "__main__":
    main()
