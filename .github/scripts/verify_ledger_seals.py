#!/usr/bin/env python3
"""Tri-state seal verifier for hex-bearing ledger entries. Rev 2.

Adds opt-in --require N (repeatable): exit 1 if entry N (entry_index or
filename stem) is not present among seal_sha3_256-bearing entries. This
closes the same empty/absent-ledger hole that --require closes in
scripts/verify_chain.py, which is documented there but wired into no
workflow on this branch (dormant gate - see ledger-seal-gate.yml).

Contract:
  exit 0  every ledger/*.yaml entry carrying seal_sha3_256 recomputes to
          its stored digest, and all --require'd entries are present.
          Entries without seal_sha3_256 are legacy non-events: reported
          and skipped, never verified.
  exit 1  any recomputed digest mismatches its stored seal_sha3_256,
          a ledger file is not parseable YAML, or a --require'd entry is
          missing (including the empty-ledger case).
  exit 2  no ledger/*.yaml files present at all.

Canonical body: json.dumps(body, sort_keys=True, separators=(",", ":"))
where body = the entry mapping minus the seal_sha3_256 field.

This verifier can fail. That is its purpose.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("FAIL: PyYAML required (python -c 'import yaml')")
    sys.exit(1)

SEAL_FIELD = "seal_sha3_256"


def canonical_body(entry: dict) -> str:
    body = {k: v for k, v in entry.items() if k != SEAL_FIELD}
    return json.dumps(body, sort_keys=True, separators=(",", ":"))


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Verify seal_sha3_256 digests on ledger entries."
    )
    ap.add_argument("root", nargs="?", default=".",
                    help="Repository root (default: .)")
    ap.add_argument("--require", type=int, action="append", default=None,
                    metavar="N",
                    help="Exit 1 if entry N is not present among sealed "
                         "entries. Repeatable.")
    args = ap.parse_args()

    root = Path(args.root)
    ledger_dir = root / "ledger"
    files = sorted(ledger_dir.glob("*.yaml")) if ledger_dir.is_dir() else []
    if not files:
        print("FAIL: no ledger/*.yaml present - nothing to check")
        return 2

    verified = 0
    legacy = 0
    present_indices = set()
    for path in files:
        try:
            entry = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except Exception as exc:
            print(f"FAIL: {path}: unparseable YAML: {exc}")
            return 1
        if not isinstance(entry, dict):
            print(f"- {path}: non-mapping - skipped")
            continue
        if path.stem.isdigit():
            present_indices.add(int(path.stem))
        ei = entry.get("entry_index")
        if isinstance(ei, int):
            present_indices.add(ei)
        stored = entry.get(SEAL_FIELD)
        if not isinstance(stored, str) or len(stored) != 64:
            legacy += 1
            continue
        computed = hashlib.sha3_256(
            canonical_body(entry).encode("utf-8")
        ).hexdigest()
        if computed != stored.lower():
            print(f"FAIL: {path}: seal mismatch")
            print(f"  stored:   {stored}")
            print(f"  computed: {computed}")
            return 1
        verified += 1

    missing = [n for n in (args.require or []) if n not in present_indices]
    if missing:
        for n in missing:
            print(f"FAIL: required entry {n} not present in {ledger_dir}/")
        return 1

    req = f", required present: {args.require}" if args.require else ""
    print(
        f"OK: {verified} sealed entr(ies) verified, "
        f"{legacy} legacy entr(ies) skipped (no {SEAL_FIELD}){req}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
