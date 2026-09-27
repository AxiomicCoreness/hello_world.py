#!/usr/bin/env python3
"""
verify_prev_hash.py — the gate-side half of the prev_hash chain.

Companion to .github/scripts/verify_ledger_seals.py.
Implements the concatenation rule recorded verbatim at entry 8984:

    H_n = sha3_256(canonical_json(entry_n minus seal and prev_hash fields))
    entry_{n+1}.prev_hash = H_n
    gate verifies: entry_{n+1}.prev_hash == sha3_256(canonical body of entry_n)

DECLARED_INTENT, NOT WIRED UNTIL VALIDATED:
This script could not be reconciled against the existing gate in the
session that authored it (the connector returned blob SHAs only, not
file bytes). Before this becomes mechanism:

    1. It MUST reproduce H_8983 = 2a459ea5... byte-identical from the
       landed 8983 entry (validate-against-known-good, pattern 8).
    2. Its canonicalisation MUST be compared field-by-field with the
       gate that produced the landed seals. If they differ, the gate's
       canonicalisation is authoritative; this script is corrected or
       retired.
    3. Wiring it into CI is an explicit, recorded decision (Contract C).

Until all three hold, this is a described instrument, not a gate.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

LEDGER_DIR = Path(__file__).resolve().parents[2] / "ledger"
EXCLUDED_FIELDS = {"seal", "prev_hash"}

# Known-good anchor: the 8983 seal reproduced at the 8984 forge.
KNOWN_GOOD = {"index": "8983", "expected_sha3_256_prefix": "2a459ea5"}


def canonical_body(entry: dict) -> bytes:
    """Canonical JSON of an entry minus 'seal' and 'prev_hash' fields."""
    body = {k: v for k, v in entry.items() if k not in EXCLUDED_FIELDS}
    return json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha3_256(data: bytes) -> str:
    return hashlib.sha3_256(data).hexdigest()


def load_entry(index: str) -> dict:
    """Load ledger/<index>.yaml and parse its fields as a dict.

    Ledger entries use a mix of nested YAML. Minimal parse: top-level
    key: value lines plus embedded JSON where present. The authoritative
    parse is whatever the existing gate uses — see DECLARED_INTENT note.
    """
    path = LEDGER_DIR / f"{int(index):04d}.yaml"
    if not path.exists():
        path = LEDGER_DIR / f"{index}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"ledger entry not found: {index}")
    text = path.read_text(encoding="utf-8")

    # Minimal YAML-top-level extraction: 'key: value' pairs at column 0.
    entry: dict = {}
    for line in text.splitlines():
        m = re.match(r"^([A-Za-z_][\w]*):\s*(.*)$", line)
        if m:
            key, raw = m.group(1), m.group(2).strip()
            entry[key] = raw.strip('"').strip("'")
    return entry


def verify_chain(start: int, end: int) -> list[tuple[str, str, bool]]:
    """Verify prev_hash links from start..end. Returns (n, prev_field, ok)."""
    results = []
    for n in range(start, end):
        try:
            cur = load_entry(str(n))
            nxt = load_entry(str(n + 1))
        except FileNotFoundError as e:
            results.append((str(n), f"missing: {e}", False))
            continue

        computed = sha3_256(canonical_body(cur))
        claimed = str(nxt.get("prev_hash", "")).strip('"').strip("'")
        ok = claimed == computed and claimed != ""
        results.append((str(n), claimed[:24] if claimed else "<none>", ok))
    return results


def self_check() -> bool:
    """Validate-against-known-good: reproduce the 8983 seal prefix."""
    try:
        entry = load_entry(KNOWN_GOOD["index"])
    except FileNotFoundError:
        print("[self-check] 8983 not found locally — cannot validate. NOT A GATE.")
        return False
    computed = sha3_256(canonical_body(entry))
    ok = computed.startswith(KNOWN_GOOD["expected_sha3_256_prefix"])
    print(f"[self-check] H_8983 = {computed}")
    print(f"[self-check] expected prefix: {KNOWN_GOOD['expected_sha3_256_prefix']} — {'MATCH' if ok else 'MISMATCH'}")
    if not ok:
        print("[self-check] canonicalisation differs from the landed gate. "
              "The gate's canonicalisation is authoritative. NOT A GATE.")
    return ok


def main() -> int:
    print("=" * 72)
    print("verify_prev_hash.py — chain-link verifier (DECLARED_INTENT)")
    print("=" * 72)
    if not self_check():
        return 2

    start, end = 8984, 9251  # prev_hash chain region
    results = verify_chain(start, end)
    broken = [r for r in results if not r[2]]
    for n, prev, ok in results:
        mark = "OK " if ok else "BROKEN"
        print(f"  [{mark}] {n} -> prev_hash {prev}")
    print("-" * 72)
    if broken:
        print(f"CHAIN BROKEN at {len(broken)} link(s): {[b[0] for b in broken]}")
        return 1
    print(f"CHAIN VERIFIED: {start} -> {end} — every link computed, none asserted.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
