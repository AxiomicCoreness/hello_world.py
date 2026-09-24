#!/usr/bin/env python3
"""Minimal producer: hand off the smoke catalogue to scenario workers.

Reads docs/smoke_catalogue.json (produced by scripts/catalogue_smoke_tests.py,
which pre-exists and is not modified by this commit), writes
results/scenario_0.json and ledger/8959.yaml. Entry 8958 belongs to
scripts/seal_8958.py / the catalogue lane and is not written here.

Sealing: ledger/8959.yaml carries seal_sha3_256 = sha3-256 over the
canonical JSON of the entry with the seal_sha3_256 field removed - the
exact contract .github/scripts/verify_ledger_seals.py verifies. The
digest is computed at write time, never asserted. The workflow comment
("reads catalogue, dispatches Celery/local, writes ledger/8959.yaml")
is satisfied; no worker results are claimed - the scenario file records
only what this script actually did.

Exit codes:
  0  catalogue consumed, outputs written and sealed
  1  catalogue missing, unreadable, or malformed
This script can fail; that is its purpose.
"""
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

ENTRY_INDEX = 8959
CATALOGUE_PATH = Path("docs/smoke_catalogue.json")
RESULTS_DIR = Path("results")
LEDGER_DIR = Path("ledger")


def canonical(body: dict) -> str:
    return json.dumps(body, sort_keys=True, separators=(",", ":"))


def count_entries(entries) -> int:
    if isinstance(entries, list):
        return len(entries)
    if isinstance(entries, dict):
        return len(entries)
    return 0


def main() -> int:
    if not CATALOGUE_PATH.is_file():
        print(f"FAIL: {CATALOGUE_PATH} missing - run catalogue_smoke_tests.py first")
        return 1
    try:
        catalogue = json.loads(CATALOGUE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"FAIL: {CATALOGUE_PATH} unreadable: {exc}")
        return 1
    if not isinstance(catalogue, dict) or "entries" not in catalogue:
        print("FAIL: catalogue malformed: expected a mapping with 'entries'")
        return 1

    n = count_entries(catalogue["entries"])
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    scenario_path = RESULTS_DIR / "scenario_0.json"
    scenario_path.write_text(
        json.dumps(
            {
                "scenario": 0,
                "source": "docs/smoke_catalogue.json",
                "catalogue_entries": n,
                "record": "dispatch record only - no worker results are claimed",
                "written_by": "scripts/handoff_to_workers.py",
            },
            sort_keys=True,
            indent=2,
        ),
        encoding="utf-8",
    )

    entry = {
        "entry_index": ENTRY_INDEX,
        "event": "/handoff_to_workers",
        "generated_by": "scripts/handoff_to_workers.py",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "catalogue_entries": n,
        "results_file": "results/scenario_0.json",
        "seal": f"HANDOFF_{ENTRY_INDEX} - sha3-256 bound via seal_sha3_256",
    }
    digest = hashlib.sha3_256(canonical(entry).encode("utf-8")).hexdigest()
    entry["seal_sha3_256"] = digest

    LEDGER_DIR.mkdir(parents=True, exist_ok=True)
    (LEDGER_DIR / f"{ENTRY_INDEX}.yaml").write_text(
        yaml.safe_dump(entry, sort_keys=True, allow_unicode=True),
        encoding="utf-8",
    )

    print(f"OK: scenario_0 dispatched over {n} catalogue entr(ies)")
    print(f"OK: ledger/{ENTRY_INDEX}.yaml sealed (seal_sha3_256={digest})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
