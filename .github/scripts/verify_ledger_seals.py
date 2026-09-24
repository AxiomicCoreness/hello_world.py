#!/usr/bin/env python3
"""Tri-state seal verifier for hex-bearing ledger entries.

Distinct from verify_ledger.py (Regime A/B seal verifier) - that path is
occupied and must not be clobbered (see verify_ledger_math.py header).
Manifest named this file verify_ledger.py; landed under a new path for
that reason. Renaming was required by collision, not used as remediation.

Contract:
  exit 0  every ledger/*.yaml entry carrying seal_sha3_256 recomputes to
          its stored digest. Entries without seal_sha3_256 are legacy
          non-events: reported and skipped, never verified.
  exit 1  any recomputed digest mismatches its stored seal_sha3_256
          (body changed without resealing), or a ledger file is not
          parseable YAML.
  exit 2  no ledger/*.yaml files present at all (nothing to check).
          Manifest offered vacuous-0 or explicit-2; explicit-2 chosen,
          matching the timestamp-beacon precedent.

Canonical body: json.dumps(body, sort_keys=True, separators=(",", ":"))
where body = the entry mapping minus the seal_sha3_256 field.
Digest: sha3-256 of the canonical body, UTF-8. seal_sha3_256 is the
digest-field convention already recognized by scripts/verify_chain.py
(DIGEST_KEYS) and scripts/seal_ledger_entry.py.

This verifier can fail. That is its purpose.
"""
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
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    ledger_dir = root / "ledger"
    files = sorted(ledger_dir.glob("*.yaml")) if ledger_dir.is_dir() else []
    if not files:
        print("FAIL: no ledger/*.yaml present - nothing to check")
        return 2

    verified = 0
    legacy = 0
    for path in files:
        try:
            entry = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except Exception as exc:
            print(f"FAIL: {path}: unparseable YAML: {exc}")
            return 1
        if not isinstance(entry, dict):
            print(f"- {path}: non-mapping - skipped")
            continue
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

    print(
        f"OK: {verified} sealed entr(ies) verified, "
        f"{legacy} legacy entr(ies) skipped (no {SEAL_FIELD})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
