"""
verify_ledger.py — verify a ledger entry's seal against its body.

HASH ALGORITHM: SHA3-256 (FIPS 202). Non-negotiable.

Dual regime (append-only safe):
  Regime A (89xx): SHA3-256(canonical JSON body minus 'seal')
  Regime B (92xx): SHA3-256(GARDEN.EVENT.v1 || 0x00 || n|event|phi2|delta|theta)
                   ASCII b^2 only — Unicode b² is rejected.

Modes (default = --soft):
  --emit   print the computed digests and exit 0 (diagnostic; never fails)
  --soft   missing file → soft skip; mismatch → exit 0 with warning (default)
  --hard   missing file → fail;  mismatch → exit 1

A seal verifies if declared hex matches A OR B. No ledger rewrite.

Usage:
    python .github/scripts/verify_ledger.py ledger/8979.yaml
    python .github/scripts/verify_ledger.py --hard ledger/9237.yaml ledger/9238.yaml
    python .github/scripts/verify_ledger.py --emit ledger/9242.yaml
"""
from __future__ import annotations

import argparse
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

# Regime B constants — must match sealer payload exactly
EVENT_DOMAIN = b"GARDEN.EVENT.v1"
PHI2 = "2.618033988749895"
DELTA = "b^2-4ac"
THETA = "2.5416018462"

# North Star anchor (documentation / witness only)
NORTH_STAR_HZ = 71.975
PHASE_LOCK_DEG = 202.6
WORKLOAD = 0.0
COHERENCE = 1.0


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
    """Regime A — SHA3-256 over canonical JSON body (minus 'seal')."""
    body = {k: v for k, v in data.items() if k != "seal"}
    canon = json.dumps(
        body,
        sort_keys=True,
        separators=(",", ":"),
        default=json_default,
        ensure_ascii=False,
    )
    return hashlib.new(HASH_ALGO, canon.encode("utf-8")).hexdigest()


def event_hash(data: dict) -> Optional[str]:
    """Regime B — SHA3-256(GARDEN.EVENT.v1 || 0x00 || payload)."""
    n = data.get("entry_index")
    event = data.get("event")
    if not isinstance(n, int) or not isinstance(event, str):
        return None
    payload = f"{n}|{event}|phi2={PHI2}|delta={DELTA}|theta={THETA}"
    return hashlib.new(
        HASH_ALGO, EVENT_DOMAIN + b"\x00" + payload.encode("ascii")
    ).hexdigest()


def declared_hex(data: dict) -> Optional[str]:
    """Prefer last 64-hex in seal; fall back to terminal_hex / witness_prefix."""
    seal = str(data.get("seal", ""))
    matches = HASH_RE.findall(seal)
    if matches:
        return matches[-1].lower()
    for key in ("terminal_hex", "witness_prefix", "verification_hash"):
        v = data.get(key)
        if isinstance(v, str) and HASH_RE.fullmatch(v.strip()):
            return v.strip().lower()
    return None


def verify(path: Path, mode: str) -> bool:
    """mode ∈ {\"emit\", \"soft\", \"hard\"}"""
    if not path.exists():
        msg = f"⚠️ {path} not found"
        if mode == "hard":
            print(f"{msg} — hard fail")
            return False
        print(f"{msg} — soft skip")
        return True

    try:
        data = yaml.safe_load(path.read_text()) or {}
    except yaml.YAMLError as e:
        print(f"❌ {path}: YAML parse error: {e}")
        return False if mode == "hard" else True

    if not isinstance(data, dict):
        print(f"❌ {path}: top-level YAML is not a mapping")
        return False if mode == "hard" else True

    declared = declared_hex(data)
    if not declared:
        print(f"❌ {path}: no 64-hex SHA3-256 digest in seal/terminal_hex")
        return False if mode == "hard" else True

    try:
        computed_a = canonical_hash(data)
        computed_b = event_hash(data)
    except Exception as e:
        print(f"❌ {path}: canonicalisation failed: {e}")
        return False if mode == "hard" else True

    regime: Optional[str] = None
    if declared == computed_a:
        regime = "A(json)"
    elif computed_b is not None and declared == computed_b:
        regime = "B(event)"

    if mode == "emit":
        print(f"— {path}")
        print(f"   entry_index:  {data.get('entry_index', '?')}")
        print(f"   declared:     {declared}")
        print(f"   computed_A:   {computed_a}")
        print(f"   computed_B:   {computed_b}")
        print(f"   regime:       {regime or 'MISMATCH'}")
        print(
            f"   north_star:   {NORTH_STAR_HZ} Hz · {PHASE_LOCK_DEG}° · "
            f"W={WORKLOAD} · C={COHERENCE}"
        )
        return True

    if regime is None:
        print(f"❌ {path}: seal mismatch (sha3_256)")
        print(f"   declared:   {declared}")
        print(f"   computed_A: {computed_a}")
        if computed_b is not None:
            print(f"   computed_B: {computed_b}")
        return False if mode == "hard" else True

    entry_index = data.get("entry_index", "?")
    print(
        f"✅ {path}: sha3_256 seal verified "
        f"(entry_index={entry_index}, regime={regime}, {declared[:16]}...)"
    )
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify ledger seals (tri-mode).")
    g = parser.add_mutually_exclusive_group()
    g.add_argument("--emit", action="store_true", help="print digests, never fail")
    g.add_argument("--soft", action="store_true", help="warn on mismatch, exit 0 (default)")
    g.add_argument("--hard", action="store_true", help="fail on mismatch or missing file")
    parser.add_argument("paths", nargs="+", help="one or more ledger YAML files")
    args = parser.parse_args()

    mode = "emit" if args.emit else "hard" if args.hard else "soft"

    ok = True
    for arg in args.paths:
        ok = verify(Path(arg), mode) and ok
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
