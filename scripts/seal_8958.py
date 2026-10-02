#!/usr/bin/env python3
"""scripts/seal_8958.py — write ledger/8958.yaml with seal_sha3_256.

Ceremonial seal string is a label. The verifiable field is seal_sha3_256,
sha3-256 over the canonical body with that field excluded.
status is FAILED when the catalogue records all_passed false.
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


def canonical(body: dict) -> str:
    return json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def main() -> None:
    path = Path(LEDGER_DIR) / "8958.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    Path("docs").mkdir(exist_ok=True)

    catalogue = Path("docs/smoke_catalogue.json")
    catalogue_digest = ""
    all_passed = False
    if catalogue.exists():
        raw = catalogue.read_bytes()
        catalogue_digest = hashlib.sha3_256(raw).hexdigest()
        try:
            parsed = json.loads(raw.decode("utf-8"))
            if isinstance(parsed, dict):
                all_passed = bool(parsed.get("all_passed"))
        except Exception:
            all_passed = False

    entry = {
        "entry_index": 8958,
        "event": "/generate_smoke_catalogue",
        "status": "PASSED" if all_passed else "FAILED",
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "hash_algo": HASH_ALGO,
        "catalogue_path": "docs/smoke_catalogue.json",
        "catalogue_sha3_256": catalogue_digest,
        "revived_from": "de3e470642bdce51050141707e103a336c1f1530",
    }
    entry["seal_sha3_256"] = hashlib.sha3_256(
        canonical(entry).encode("utf-8")
    ).hexdigest()

    path.write_text(
        yaml.safe_dump(entry, sort_keys=True, allow_unicode=True),
        encoding="utf-8",
    )
    print("Ledger entry 8958 written.")
    print(f"seal_sha3_256: {entry['seal_sha3_256']}")
    print(f"status: {entry['status']}")
    print(f"catalogue_sha3_256: {catalogue_digest or '(none)'}")


if __name__ == "__main__":
    main()
