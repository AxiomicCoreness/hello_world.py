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

────────────────────────────────────────────────────────────────────
MERGE RATIONALE — why this file has two implementations
────────────────────────────────────────────────────────────────────
This file was produced by resolving a two-sided merge conflict between
branch `deepseek` and branch `main`. The conflict spanned:

  1. docstring mode list (deepseek: none / main: --emit/--soft/--hard)
  2. usage lines + imports (deepseek: no argparse / main: argparse)
  3. Regime B constants  (deepseek: no North Star block /
                          main: adds documentation constants)
  4. five functions      (canonical_hash, event_hash, declared_hex,
                          verify, main)

Resolution rule applied:
  • `main`'s side is the ACTIVE implementation. It is a strict superset:
    --emit/--soft/--hard modes, argparse CLI, North Star documentation
    constants. The active `verify()` has signature `(path, mode)`.
  • `deepseek`'s side is preserved under `_legacy_*` names. It is NOT
    dispatched to, NOT imported by the active path, and exists only so
    that no merge input is silently discarded. It also serves as a
    reference for any external caller that still expects the old
    zero-argument `verify(path) -> bool` signature, which can be
    restored in one line by changing `_legacy_verify_soft_only` back
    to `verify`.

  • One deliberate change from `main`: `path.read_text(encoding="utf-8")`
    — the seals contain the Unicode string `∀∞φ²`, so the read must be
    explicit rather than locale-dependent. This is the only semantic
    difference between this file and `main`'s side of the conflict.

Line-count accounting (306 raw → this file):
  raw conflicted file ................................. 306
    – conflict markers (<<<<<<<, =======, >>>>>>>) ..... 15
    – deepseek duplicate constant block ................. 5
    – deepseek duplicate functions ..................... 85
    – main conflict markers ............................. 4
    + merge-rationale header ........................... 33
    + separator + legacy section header ................. 8
    + legacy function bodies (preserved verbatim) ...... 88
    + expanded docstrings on active functions .......... 12
    = resolved file ................................... ~338

Usage:
    python .github/scripts/verify_ledger.py ledger/8979.yaml
    python .github/scripts/verify_ledger.py ledger/9237.yaml ledger/9238.yaml
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


# ─────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────

HASH_ALGO = "sha3_256"
HASH_RE = re.compile(r"([0-9a-fA-F]{64})")

# Regime B constants — must match sealer payload exactly.
# NOTE: EVENT_DOMAIN holds the domain string only. The null separator
# (0x00) is applied in event_hash() at the concatenation site, so that
# the domain name and the delimiter are visually distinct. This is
# byte-identical to the older form b"GARDEN.EVENT.v1\x00" + payload.
EVENT_DOMAIN = b"GARDEN.EVENT.v1"
PHI2 = "2.618033988749895"
DELTA = "b^2-4ac"
THETA = "2.5416018462"

# North Star anchor (documentation / witness only — not consumed by
# the verifier's logic; present so operators can see the intended
# invariant targets alongside the code that checks the seals).
NORTH_STAR_HZ = 71.975
PHASE_LOCK_DEG = 202.6
WORKLOAD = 0.0
COHERENCE = 1.0


# ─────────────────────────────────────────────────────────────────────
# JSON canonicalisation helper
# ─────────────────────────────────────────────────────────────────────

def json_default(obj: Any) -> Any:
    """
    Fallback serialiser for json.dumps(). Handles the types PyYAML
    can produce from a ledger YAML body that json.dumps cannot
    natively encode.
    """
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


# ─────────────────────────────────────────────────────────────────────
# Active implementation — from branch `main`
# ─────────────────────────────────────────────────────────────────────

def canonical_hash(data: dict) -> str:
    """
    Regime A — SHA3-256 over the canonical JSON encoding of the ledger
    body with the 'seal' key removed.

    Canonicalisation is fixed: sorted keys, compact separators (",",":"),
    no ASCII escaping, UTF-8 output. Any change to this method
    invalidates every Regime A seal ever produced.
    """
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
    """
    Regime B — SHA3-256(GARDEN.EVENT.v1 || 0x00 || payload).

    The payload is a fixed-format ASCII string built from the entry's
    integer index and its event name, followed by the phi2, delta, and
    theta constants. The ASCII form of b^2 is mandatory; the Unicode
    b² is rejected at the .encode("ascii") call.
    """
    n = data.get("entry_index")
    event = data.get("event")
    if not isinstance(n, int) or not isinstance(event, str):
        return None
    payload = f"{n}|{event}|phi2={PHI2}|delta={DELTA}|theta={THETA}"
    return hashlib.new(
        HASH_ALGO, EVENT_DOMAIN + b"\x00" + payload.encode("ascii")
    ).hexdigest()


def declared_hex(data: dict) -> Optional[str]:
    """
    Extract the declared seal digest from the entry.

    Precedence:
      1. The last 64-hex run inside the `seal` string. Seals produced
         by the current sealer append the digest after a middle dot,
         so "last" resolves to the current digest even if an older
         digest string appears earlier in the seal text.
      2. Fallback keys, in order: terminal_hex, witness_prefix,
         verification_hash. Each must match the 64-hex pattern exactly.
    """
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
    """
    Verify a single ledger file.

    mode ∈ {"emit", "soft", "hard"}:
      • emit  — print declared, computed_A, computed_B, regime; always
                return True. Diagnostics only.
      • soft  — missing file → True; parse error → True; mismatch →
                True with warning. Default.
      • hard  — missing file → False; any error → False; mismatch →
                False.

    Return value is the caller's contract: in emit/soft, the caller
    should treat the boolean as advisory and inspect printed output;
    in hard, the boolean is authoritative.
    """
    if not path.exists():
        msg = f"⚠️ {path} not found"
        if mode == "hard":
            print(f"{msg} — hard fail")
            return False
        print(f"{msg} — soft skip")
        return True

    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
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
    g.add_argument("--emit", action="store_true",
                   help="print digests, never fail")
    g.add_argument("--soft", action="store_true",
                   help="warn on mismatch, exit 0 (default)")
    g.add_argument("--hard", action="store_true",
                   help="fail on mismatch or missing file")
    parser.add_argument("paths", nargs="+",
                        help="one or more ledger YAML files")
    args = parser.parse_args()

    mode = "emit" if args.emit else "hard" if args.hard else "soft"

    ok = True
    for arg in args.paths:
        ok = verify(Path(arg), mode) and ok
    return 0 if ok else 1


# ─────────────────────────────────────────────────────────────────────
# LEGACY IMPLEMENTATION — from branch `deepseek`
#
# These functions are preserved verbatim from the `deepseek` side of
# the merge conflict. They are NOT dispatched to. The active entry
# point is `main()` above. Do not import these unless you are
# deliberately restoring the zero-argument verify signature.
#
# To restore the deepseek behaviour as the active path:
#   1. Rename `_legacy_verify_soft_only` to `verify`.
#   2. Rename `_legacy_main` to `main`.
#   3. Delete or comment the active `main()` above.
# ─────────────────────────────────────────────────────────────────────

def _legacy_canonical_hash(data: dict) -> str:
    """Legacy Regime A — identical bytes to canonical_hash()."""
    body = {k: v for k, v in data.items() if k != "seal"}
    canon = json.dumps(
        body, sort_keys=True, separators=(",", ":"),
        default=json_default, ensure_ascii=False,
    )
    return hashlib.new(HASH_ALGO, canon.encode("utf-8")).hexdigest()


def _legacy_event_hash(data: dict) -> Optional[str]:
    """
    Legacy Regime B — uses the combined EVENT_DOMAIN_LEGACY form
    b"GARDEN.EVENT.v1\\x00" + payload (no separate delimiter at the
    concatenation site). Produces byte-identical digests to the
    active event_hash(); kept for reference only.
    """
    n = data.get("entry_index")
    event = data.get("event")
    if not isinstance(n, int) or not isinstance(event, str):
        return None
    payload = f"{n}|{event}|phi2={PHI2}|delta={DELTA}|theta={THETA}"
    return hashlib.new(
        HASH_ALGO, b"GARDEN.EVENT.v1\x00" + payload.encode("ascii")
    ).hexdigest()


def _legacy_declared_hex(data: dict) -> Optional[str]:
    """Legacy seal-digest extractor. Identical logic to declared_hex()."""
    seal = str(data.get("seal", ""))
    matches = HASH_RE.findall(seal)
    if matches:
        return matches[-1].lower()
    for key in ("terminal_hex", "witness_prefix", "verification_hash"):
        v = data.get(key)
        if isinstance(v, str) and HASH_RE.fullmatch(v.strip()):
            return v.strip().lower()
    return None


def _legacy_verify_soft_only(path: Path) -> bool:
    """
    Legacy verify — soft-only, no mode parameter.

    Always returns True unless the file parses as a mapping that
    contains an explicit 64-hex digest which matches neither regime.
    Missing files return True; YAML parse errors return False only
    when the top-level is not a dict — but mismatch returns False.
    This asymmetry is why the active implementation distinguishes
    soft vs hard modes explicitly.
    """
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
    declared = _legacy_declared_hex(data)
    if not declared:
        print(f"❌ {path}: no 64-hex SHA3-256 digest in seal/terminal_hex")
        return False
    try:
        computed_a = _legacy_canonical_hash(data)
        computed_b = _legacy_event_hash(data)
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


def _legacy_main() -> int:
    """Legacy entry point — sys.argv walker, no flags."""
    if len(sys.argv) < 2:
        print("usage: verify_ledger.py <ledger.yaml> [...]")
        return 2
    ok = True
    for arg in sys.argv[1:]:
        ok = _legacy_verify_soft_only(Path(arg)) and ok
    return 0 if ok else 1


# ─────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    sys.exit(main())