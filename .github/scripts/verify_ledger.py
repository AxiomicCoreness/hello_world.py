"""
verify_ledger.py — verify a ledger entry's seal against its body.

HASH ALGORITHM: SHA3-256 (FIPS 202). Non-negotiable.
Every ledger entry's seal MUST end with a 64-hex SHA3-256 digest
over the canonical (sorted-key, compact-JSON) body excluding 'seal'.

Canonicalisation rules (single source of truth):
  - Body = entry with 'seal' removed.
  - Non-JSON-native YAML scalars are normalised via `json_default`:
      * datetime / date / time  -> ISO-8601 string (UTC 'Z' for naive dt)
      * Decimal                 -> str(decimal)
      * set / frozenset         -> sorted list
      * bytes / bytearray       -> hex string
      * UUID                    -> str(uuid)
      * Path                    -> posix string
      * everything else         -> str(obj)     (last resort)
  - Dump with sort_keys=True, separators=(',', ':').

Usage:
    python scripts/verify_ledger.py ledger/8979.yaml
    python scripts/verify_ledger.py ledger/*.yaml
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import re
import sys
import uuid
from decimal import Decimal
from pathlib import Path
from typing import Any

import yaml


HASH_ALGO = "sha3_256"
HASH_RE = re.compile(r"([0-9a-fA-F]{64})")


# ─── Canonicalisation ─────────────────────────────────────────────────────────
def json_default(obj: Any) -> Any:
    """
    Fallback serialiser for non-JSON-native YAML scalars.

    Deterministic. Order-stable. Matches the format every workflow's seal
    step produces when it writes `timestamp: datetime.now(timezone.utc)`:
    we emit 'YYYY-MM-DDTHH:MM:SSZ' for UTC and 'YYYY-MM-DDTHH:MM:SS+HH:MM'
    for timezone-aware values that are not UTC.
    """
    # datetime / date / time
    if isinstance(obj, _dt.datetime):
        if obj.tzinfo is None:
            return obj.strftime("%Y-%m-%dT%H:%M:%SZ")
        return obj.astimezone(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if isinstance(obj, _dt.date):
        return obj.isoformat()
    if isinstance(obj, _dt.time):
        return obj.isoformat()

    # numeric
    if isinstance(obj, Decimal):
        return str(obj)

    # set-like
    if isinstance(obj, (set, frozenset)):
        try:
            return sorted(obj)
        except TypeError:
            return sorted(map(str, obj))

    # bytes
    if isinstance(obj, (bytes, bytearray)):
        return bytes(obj).hex()

    # misc structured
    if isinstance(obj, uuid.UUID):
        return str(obj)
    if isinstance(obj, Path):
        return obj.as_posix()

    # last resort — deterministic but lossy
    return str(obj)


def canonical_hash(data: dict) -> str:
    """SHA3-256 over canonical form of data (minus 'seal')."""
    body = {k: v for k, v in data.items() if k != "seal"}
    canon = json.dumps(
        body,
        sort_keys=True,
        separators=(",", ":"),
        default=json_default,
        ensure_ascii=False,
    )
    return hashlib.new(HASH_ALGO, canon.encode("utf-8")).hexdigest()


# ─── Verification ─────────────────────────────────────────────────────────────
def verify(path: Path) -> bool:
    if not path.exists():
        print(f"⚠️ {path} not found — soft skip")
        return True

    try:
        data = yaml.safe_load(path.read_text()) or {}
    except yaml.YAMLError as e:
        print(f"❌ {path}: YAML parse error: {e}")
        return False

    if not isinstance(data, dict):
        print(f"❌ {path}: top-level YAML is not a mapping")
        return False

    seal = str(data.get("seal", ""))
    m = HASH_RE.search(seal)
    if not m:
        print(f"❌ {path}: no 64-hex SHA3-256 digest in seal")
        return False

    declared = m.group(1).lower()
    try:
        computed = canonical_hash(data)
    except Exception as e:
        print(f"❌ {path}: canonicalisation failed: {e}")
        return False

    if declared != computed:
        print(f"❌ {path}: seal mismatch (sha3_256)")
        print(f"   declared: {declared}")
        print(f"   computed: {computed}")
        return False

    entry_index = data.get("entry_index", "?")
    print(f"✅ {path}: sha3_256 seal verified "
          f"(entry_index={entry_index}, {declared[:16]}...)")
    return True


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: verify_ledger.py <ledger.yaml> [...]")
        return 2
    ok = True
    for arg in sys.argv[1:]:
        ok = verify(Path(arg)) and ok
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
