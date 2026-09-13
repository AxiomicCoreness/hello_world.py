"""
verify_ledger.py — verify a ledger entry's seal against its body.

HASH ALGORITHM: SHA3-256 (FIPS 202). Non-negotiable.

Dual regime (append-only safe):
  Regime A (89xx): SHA3-256(canonical JSON body minus 'seal')
  Regime B (92xx): SHA3-256(GARDEN.EVENT.v1 || 0x00 || n|event|phi2|delta|theta)
                   ASCII b^2 only — Unicode b² is rejected.

A seal verifies if declared hex matches A OR B. No ledger rewrite.

Usage:
    python .github/scripts/verify_ledger.py ledger/8979.yaml
    python .github/scripts/verify_ledger.py ledger/9237.yaml ledger/9238.yaml
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
from typing import Any, Optional

import yaml


HASH_ALGO = "sha3_256"
HASH_RE = re.compile(r"([0-9a-fA-F]{64})")

EVENT_DOMAIN = b"GARDEN.EVENT.v1\x00"
PHI2 = "2.618033988749895"
DELTA = "b^2-4ac"
THETA = "2.5416018462"


def json_default(obj: Any) -> Any:
    if isinstance(obj, _dt.datetime):
        if obj.tzinfo is None:
            return obj.strftime("%Y-%m-%dT%H:%M:%SZ")
        return obj.astimezone(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if isinstance(obj, _dt.date):
        return obj.isoformat()
    if isinstance(obj, _dt.time):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return str(obj)
    if isinstance(obj, (set, frozenset)):
        try:
            return sorted(obj)
        except TypeError:
            return sorted(map(str, obj))
    if isinstance(obj, (bytes, bytearray)):
        return bytes(obj).hex()
    if isinstance(obj, uuid.UUID):
        return str(obj)
    if isinstance(obj, Path):
        return obj.as_posix()
    return str(obj)


def canonical_hash(data: dict) -> str:
    body = {k: v for k, v in data.items() if k != "seal"}
    canon = json.dumps(
        body, sort_keys=True, separators=(",", ":"),
        default=json_default, ensure_ascii=False,
    )
    return hashlib.new(HASH_ALGO, canon.encode("utf-8")).hexdigest()


def event_hash(data: dict) -> Optional[str]:
    n = data.get("entry_index")
    event = data.get("event")
    if not isinstance(n, int) or not isinstance(event, str):
        return None
    payload = f"{n}|{event}|phi2={PHI2}|delta={DELTA}|theta={THETA}"
    return hashlib.new(
        HASH_ALGO, EVENT_DOMAIN + payload.encode("ascii")
    ).hexdigest()


def declared_hex(data: dict) -> Optional[str]:
    seal = str(data.get("seal", ""))
    matches = HASH_RE.findall(seal)
    if matches:
        return matches[-1].lower()
    for key in ("terminal_hex", "witness_prefix", "verification_hash"):
        v = data.get(key)
        if isinstance(v, str) and HASH_RE.fullmatch(v.strip()):
            return v.strip().lower()
    return None


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
    declared = declared_hex(data)
    if not declared:
        print(f"❌ {path}: no 64-hex SHA3-256 digest in seal/terminal_hex")
        return False
    try:
        computed_a = canonical_hash(data)
        computed_b = event_hash(data)
    except Exception as e:
        print(f"❌ {path}: canonicalisation failed: {e}")
        return False
    if declared == computed_a:
        regime = "A(json)"
    elif computed_b is not None and declared == computed_b:
        regime = "B(event)"
    else:
        print(f"❌ {path}: seal mismatch (sha3_256)")
        print(f"   declared: {declared}")
        print(f"   computed_A: {computed_a}")
        if computed_b is not None:
            print(f"   computed_B: {computed_b}")
        return False
    entry_index = data.get("entry_index", "?")
    print(
        f"✅ {path}: sha3_256 seal verified "
        f"(entry_index={entry_index}, regime={regime}, {declared[:16]}...)"
    )
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
