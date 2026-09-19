#!/usr/bin/env python3
"""Verify ledger entry 9154 — strict form.

This script does exactly three things:

  1. Parses ledger/9154.yaml with pyyaml (no fallback parser).
  2. Recomputes SHA3-256 over the canonical body (all fields except "seal")
     and compares it to the trailing 64-hex value in the "seal" field.
  3. Reads prev_hash and checks it against the terminal hex of
     ledger/9153.yaml, if that file exists.

Every simulation field is printed as the ledger records it, or as "(absent)"
if the field is not present. There are no numeric defaults. There is no
hardcoded seal. There are no invariant claims the ledger does not carry.

Exit codes:
  0  the checks this script performs all passed
  1  a check failed
  2  a required dependency or file was missing
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("pyyaml required: python -m pip install pyyaml", file=sys.stderr)
    sys.exit(2)

HEX64 = re.compile(r"[0-9a-f]{64}")
CURRENT_INDEX = 9154
PREVIOUS_INDEX = 9153


def terminal_hex(entry: dict) -> str:
    """Return the trailing 64-hex token in the seal, or empty string."""
    matches = HEX64.findall(str(entry.get("seal", "")))
    return matches[-1] if matches else ""


def canonical_hash(entry: dict) -> str:
    """SHA3-256 over the entry body, excluding the seal field."""
    body = {k: v for k, v in entry.items() if k != "seal"}
    canon = json.dumps(body, sort_keys=True, separators=(",", ":"))
    return hashlib.sha3_256(canon.encode("utf-8")).hexdigest()


def load(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    cur_path = root / "ledger" / f"{CURRENT_INDEX}.yaml"
    prev_path = root / "ledger" / f"{PREVIOUS_INDEX}.yaml"

    if not cur_path.exists():
        print(f"{cur_path} not found", file=sys.stderr)
        return 2

    cur = load(cur_path)
    stored = terminal_hex(cur)
    computed = canonical_hash(cur)

    print(f"entry_index  = {cur.get('entry_index')}")
    print(f"event        = {cur.get('event')}")
    print(f"stored       = {stored or '(absent)'}")
    print(f"computed     = {computed}")

    if not stored:
        print("FAIL: seal contains no 64-hex token")
        return 1

    if stored != computed:
        print("FAIL: seal does not match recomputed canonical digest")
        return 1

    print("OK: seal matches recomputed canonical digest")

    # Chain link to the previous entry, if that file is present.
    if prev_path.exists():
        prev = load(prev_path)
        prev_hex = terminal_hex(prev)
        declared = str(cur.get("prev_hash", "")).strip()

        if not declared:
            print(f"WARN: prev_hash absent; chain link to {PREVIOUS_INDEX} not verified")
        elif not prev_hex:
            print(f"WARN: {prev_path.name} has no terminal hex; cannot verify chain link")
        elif declared != prev_hex:
            print(f"FAIL: prev_hash {declared[:16]}... != {prev_hex[:16]}...")
            return 1
        else:
            print(f"OK: prev_hash matches {PREVIOUS_INDEX}")
    else:
        print(f"WARN: {prev_path.name} not present; chain link not verified")

    # Report the simulation block verbatim. No defaults.
    sim = cur.get("simulation")
    if not isinstance(sim, dict):
        print("(simulation block absent)")
    else:
        print("simulation:")
        for key in sorted(sim.keys()):
            value = sim[key]
            if value is None:
                print(f"  {key} = (absent)")
            else:
                print(f"  {key} = {value}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
