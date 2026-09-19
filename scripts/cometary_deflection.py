#!/usr/bin/env python3
"""Verify ledger entry 9154 — strict form.

Checks:
  1. ledger/9154.yaml parses as YAML.
  2. entry_index equals 9154.
  3. SHA3-256 over the canonical body matches the trailing 64-hex
     token in the seal field.
  4. prev_hash (if present) matches the terminal hex of ledger/9153.yaml.
  5. Each simulation field is printed as recorded, or as "(absent)".

No numeric defaults. No hardcoded seal. No invariant claims the ledger
does not carry.

Exit codes:
  0  all checks passed
  1  a check failed
  2  a required dependency or file was missing, or a parse error
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

HEX64 = re.compile(r"[0-9a-fA-F]{64}")
CURRENT_INDEX = 9154
PREVIOUS_INDEX = 9153


def terminal_hex(entry: dict) -> str:
    matches = HEX64.findall(str(entry.get("seal", "")))
    return matches[-1].lower() if matches else ""


def canonical_hash(entry: dict) -> str:
    body = {k: v for k, v in entry.items() if k != "seal"}
    canon = json.dumps(body, sort_keys=True, separators=(",", ":"))
    return hashlib.sha3_256(canon.encode("utf-8")).hexdigest()


def load(path: Path) -> dict:
    try:
        with path.open(encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        print(f"FAIL: {path.name} YAML parse error: {e}", file=sys.stderr)
        raise
    except OSError as e:
        print(f"FAIL: {path.name} read error: {e}", file=sys.stderr)
        raise
    return data or {}


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    cur_path = root / "ledger" / f"{CURRENT_INDEX}.yaml"
    prev_path = root / "ledger" / f"{PREVIOUS_INDEX}.yaml"

    if not cur_path.exists():
        print(f"{cur_path} not found", file=sys.stderr)
        return 2

    try:
        cur = load(cur_path)
    except Exception:
        return 2

    declared_index = cur.get("entry_index")
    if declared_index != CURRENT_INDEX:
        print(
            f"FAIL: {cur_path.name} contains entry_index={declared_index}, "
            f"expected {CURRENT_INDEX}"
        )
        return 1

    stored = terminal_hex(cur)
    computed = canonical_hash(cur)

    print(f"entry_index  = {declared_index}")
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

    if prev_path.exists():
        try:
            prev = load(prev_path)
        except Exception:
            print(f"WARN: {prev_path.name} unreadable — chain link not verified")
            prev = None
        if prev is not None:
            prev_hex = terminal_hex(prev)
            declared = str(cur.get("prev_hash", "")).strip()

            if not declared:
                print(f"WARN: prev_hash absent; chain link to {PREVIOUS_INDEX} not verified")
            elif not prev_hex:
                print(f"WARN: {prev_path.name} has no terminal hex; cannot verify chain link")
            elif declared.lower() != prev_hex:
                print(f"FAIL: prev_hash {declared[:16]}... != {prev_hex[:16]}...")
                return 1
            else:
                print(f"OK: prev_hash matches {PREVIOUS_INDEX}")
    else:
        print(f"WARN: {prev_path.name} not present; chain link not verified")

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
