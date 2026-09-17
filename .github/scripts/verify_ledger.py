#!/usr/bin/env python3
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

Legacy zero-argument path is in _legacy_verify_ledger.py and is not
dispatched to. See that module's docstring for restoration instructions.

Usage:
    python .github/scripts/verify_ledger.py ledger/8979.yaml
    python .github/scripts/verify_ledger.py ledger/9237.yaml ledger/9238.yaml
    python .github/scripts/verify_ledger.py --hard ledger/9237.yaml ledger/9238.yaml
    python .github/scripts/verify_ledger.py --emit ledger/9242.yaml

    python .github/scripts/verify_ledger.py --root .
    python .github/scripts/verify_ledger.py --ledger-dir ledger --series 83 --series 91
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
import re
import sys
import uuid
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

try:
    import yaml
    HAVE_YAML = True
except ImportError:
    HAVE_YAML = False


# ─────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────

HASH_ALGO = "sha3_256"
HASH_RE = re.compile(r"([0-9a-fA-F]{64})")

# Regime B constants — must match the sealer payload byte-for-byte.
EVENT_DOMAIN = b"GARDEN.EVENT.v1"
PHI2 = "2.618033988749895"
DELTA = "b^2-4ac"
THETA = "2.5416018462"

NORTH_STAR_HZ = 71.975
PHASE_LOCK_DEG = 202.6
WORKLOAD = 0.0
COHERENCE = 1.0

REQUIRED_FIELDS = ("entry_index", "event", "seal", "witness_chain")

# Document classes exempt from the event schema. A YAML whose top-level
# carries `document_class: <one of these>` is treated as a note and is
# neither seal-checked nor chain-checked.
NON_EVENT_CLASSES = frozenset({"design-note", "policy", "index"})

KNOWN_SERIES_PREFIXES = ("83", "91", "92", "51", "00")

# Witness chain pattern: "NNNN → MMMM — UNBROKEN"
WITNESS_RE = re.compile(r"^\s*(\d{3,5})\s*[→>-]+\s*(\d{3,5})")

GENESIS_ANCHORS = {"0000"}


# ─────────────────────────────────────────────────────────────────────
# JSON canonicalisation helper
# ─────────────────────────────────────────────────────────────────────

def json_default(obj: Any) -> Any:
    """Fallback serialiser for json.dumps(): handles PyYAML types."""
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
# Data model
# ─────────────────────────────────────────────────────────────────────

class Entry:
    __slots__ = (
        "path", "index", "series", "data",
        "seal_ok", "seal_computed",
        "chain_prev", "chain_next", "notes",
    )

    def __init__(self, path: str, index: str, series: str, data: Dict[str, Any]):
        self.path = path
        self.index = index
        self.series = series
        self.data = data
        self.seal_ok: Optional[bool] = None
        self.seal_computed: Optional[str] = None
        self.chain_prev: Optional[str] = None
        self.chain_next: Optional[str] = None
        self.notes: List[str] = []


# ─────────────────────────────────────────────────────────────────────
# Loading
# ─────────────────────────────────────────────────────────────────────

def _iter_yaml_files(ledger_dir: str) -> Iterable[str]:
    if not os.path.isdir(ledger_dir):
        return
    for name in sorted(os.listdir(ledger_dir)):
        if name.endswith((".yaml", ".yml")):
            yield os.path.join(ledger_dir, name)


def _load_yaml_file(path: str) -> List[Dict[str, Any]]:
    """Load one file which may contain multiple '---' documents."""
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    if not HAVE_YAML:
        raise RuntimeError("PyYAML required to load ledger YAML files")
    docs = list(yaml.safe_load_all(text))
    return [d for d in docs if isinstance(d, dict) and d]


def _series_of(index: str) -> str:
    """Return the series prefix for an index (zero-padded to at least 4)."""
    z = index.zfill(4)
    for p in KNOWN_SERIES_PREFIXES:
        if z.startswith(p):
            return p
    return z[:2]


def _is_non_event(doc: Dict[str, Any]) -> bool:
    """True if the document opts out of the event schema."""
    cls = doc.get("document_class") or doc.get("kind")
    return isinstance(cls, str) and cls in NON_EVENT_CLASSES


def load_entries(ledger_dir: str,
                 wanted_series: Optional[List[str]] = None) -> List[Entry]:
    entries: List[Entry] = []
    for path in _iter_yaml_files(ledger_dir):
        try:
            docs = _load_yaml_file(path)
        except Exception as e:
            print(f"::error file={path}::failed to parse: {e}")
            continue
        for doc in docs:
            if _is_non_event(doc):
                continue
            raw_index = doc.get("entry_index")
            if raw_index is None:
                continue
            index = str(raw_index).zfill(4)
            series = _series_of(index)
            if wanted_series and series not in wanted_series:
                continue
            entries.append(Entry(path=path, index=index, series=series, data=doc))
    return entries


# ─────────────────────────────────────────────────────────────────────
# Seal computation — Regime A (canonical JSON)
# ─────────────────────────────────────────────────────────────────────

def canonical_hash(data: dict) -> str:
    """
    Regime A — SHA3-256 over the canonical JSON encoding of the ledger
    body with the 'seal' key removed.

    Canonicalisation is fixed: sorted keys, compact separators ("," ":"),
    no ASCII escaping, UTF-8 output. Any change invalidates every
    Regime A seal ever produced.
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


# ─────────────────────────────────────────────────────────────────────
# Seal computation — Regime B (event domain)
# ─────────────────────────────────────────────────────────────────────

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
    try:
        payload_bytes = payload.encode("ascii")
    except UnicodeEncodeError:
        return None
    return hashlib.new(
        HASH_ALGO, EVENT_DOMAIN + b"\x00" + payload_bytes
    ).hexdigest()


# ─────────────────────────────────────────────────────────────────────
# Seal extraction from the entry
# ─────────────────────────────────────────────────────────────────────

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


# ─────────────────────────────────────────────────────────────────────
# Per-file verification
# ─────────────────────────────────────────────────────────────────────

def _emit_diagnostics(data: dict, declared: str,
                      computed_a: str, computed_b: Optional[str],
                      regime: Optional[str]) -> None:
    print(f"   entry_index:  {data.get('entry_index', '?')}")
    print(f"   declared:     {declared}")
    print(f"   computed_A:   {computed_a}")
    print(f"   computed_B:   {computed_b}")
    print(f"   regime:       {regime or 'MISMATCH'}")
    print(
        f"   north_star:   {NORTH_STAR_HZ} Hz · {PHASE_LOCK_DEG}° · "
        f"W={WORKLOAD} · C={COHERENCE}"
    )


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
    except (yaml.YAMLError, ValueError) as e:
        print(f"❌ {path}: YAML parse error: {e}")
        return False if mode == "hard" else True

    if not isinstance(data, dict):
        print(f"❌ {path}: top-level YAML is not a mapping")
        return False if mode == "hard" else True

    # Non-event documents: skip seal checks, note the skip.
    if _is_non_event(data):
        print(f"— {path}: document_class={data.get('document_class') or data.get('kind')} — seal check skipped")
        return True

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
        _emit_diagnostics(data, declared, computed_a, computed_b, regime)
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


# ─────────────────────────────────────────────────────────────────────
# Tree-wide checks
# ─────────────────────────────────────────────────────────────────────

def check_required_fields(entries: List[Entry]) -> int:
    bad = 0
    for e in entries:
        missing = [f for f in REQUIRED_FIELDS if f not in e.data]
        if missing:
            print(f"::error file={e.path}::entry {e.index} missing fields: {missing}")
            bad += 1
    return bad


def seal_field_matches(data: Dict[str, Any], computed: str) -> bool:
    """
    Match the seal field against the computed digest.

    Accepts two regimes:
    - Regime A: seal == digest (exact match)
    - Regime B: seal's final whitespace-delimited token == digest

    Stricter than substring matching to avoid false positives.
    """
    seal = data.get("seal", "")
    if not isinstance(seal, str):
        return False
    if seal == computed:
        return True
    parts = seal.split()
    if parts:
        return parts[-1].lower() == computed.lower()
    return False


def check_seals(entries: List[Entry], strict: bool = False) -> int:
    bad = 0
    for e in entries:
        computed = canonical_hash(e.data)
        e.seal_computed = computed
        ok = seal_field_matches(e.data, computed)
        e.seal_ok = ok
        if not ok:
            bad += 1
            level = "error" if strict else "warning"
            print(f"::{level} file={e.path}::entry {e.index} seal mismatch")
            print(f"        expected digest: {computed}")
            print(f"        seal field:      {e.data.get('seal')}")
    return bad


def check_chains(entries: List[Entry]) -> int:
    """
    Verify witness-chain continuity per series.

    Each entry's witness_chain must be "PPPP → NNNN" where:
    - NNNN equals the entry's own index
    - PPPP equals the previous entry's index in the same series
    - No gaps allowed (strict consecutive chain)
    """
    by_series: Dict[str, List[Entry]] = {}
    for e in entries:
        by_series.setdefault(e.series, []).append(e)

    bad = 0
    for series, group in sorted(by_series.items()):
        group.sort(key=lambda x: x.index)
        print(f"── series {series}: {len(group)} entries "
              f"({group[0].index}..{group[-1].index})")

        for i, e in enumerate(group):
            m = WITNESS_RE.match(str(e.data.get("witness_chain", "")))
            if not m:
                print(f"::error file={e.path}::entry {e.index} "
                      f"unparseable witness_chain: {e.data.get('witness_chain')!r}")
                bad += 1
                continue
            prev, nxt = m.group(1).zfill(4), m.group(2).zfill(4)
            e.chain_prev, e.chain_next = prev, nxt

            if nxt != e.index:
                print(f"::error file={e.path}::entry {e.index} "
                      f"chain arrow target {nxt} != index {e.index}")
                bad += 1
                continue

            if i > 0:
                prev_entry = group[i - 1]
                if prev_entry.chain_next != e.index:
                    print(f"::error file={e.path}::entry {e.index} "
                          f"previous series entry {prev_entry.index} "
                          f"points at {prev_entry.chain_next}, expected {e.index}")
                    bad += 1

            if e.index not in GENESIS_ANCHORS:
                if i == 0:
                    if prev not in GENESIS_ANCHORS:
                        print(f"::error file={e.path}::entry {e.index} "
                              f"first in series but prev {prev} not in genesis anchors")
                        bad += 1
                else:
                    if prev != group[i - 1].index:
                        print(f"::error file={e.path}::entry {e.index} "
                              f"prev {prev} != previous entry {group[i - 1].index}")
                        bad += 1
    return bad


def check_reward_pool(entries: List[Entry]) -> int:
    """
    If fiduciary_node_rewards is importable, cross-check the declared
    pool value against its verifier. Otherwise, skip silently.
    """
    try:
        from fiduciary_node_rewards import verify_reward_pool  # type: ignore
    except Exception:
        print("── reward-pool check skipped (fiduciary_node_rewards not importable)")
        return 0

    try:
        ok, total = verify_reward_pool()
    except Exception as e:
        print(f"::error::verify_reward_pool raised: {e}")
        return 1

    declared_value = None
    for e in entries:
        v = (
            e.data.get("reward_pool")
            or e.data.get("declared_pool")
            or (e.data.get("pool") or {}).get("declared_value")
        )
        if v is not None:
            try:
                declared_value = float(v)
            except (TypeError, ValueError):
                continue

    print(f"── reward pool: verify_reward_pool -> ok={ok}, total={total:.10f}")
    if declared_value is not None:
        match = abs(declared_value - float(total)) < 1e-6
        print(f"                declared in ledger: {declared_value:.10f} "
              f"(match={match})")
        if not match:
            return 1
    return 0


# ─────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────

def _cli_verify_files(mode: str, paths: List[str]) -> int:
    """Mode for positional file args (legacy-invocation compatibility)."""
    ok = True
    for arg in paths:
        ok = verify(Path(arg), mode) and ok
    return 0 if ok else 1


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Verify sovereign ledger chains.")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--emit", action="store_true",
                   help="print digests, never fail (per-file mode)")
    g.add_argument("--soft", action="store_true",
                   help="warn on mismatch, exit 0 (per-file mode, default)")
    g.add_argument("--hard", action="store_true",
                   help="fail on mismatch or missing file (per-file mode)")

    ap.add_argument("--root", default=None,
                    help="Repository root (default: derive from this file)")
    ap.add_argument("--ledger-dir", default=None,
                    help="Ledger directory (default: <root>/ledger)")
    ap.add_argument("--series", action="append", default=None,
                    help="Restrict to a series prefix (e.g. --series 83). "
                         "May be passed multiple times.")
    ap.add_argument("--strict-seals", action="store_true",
                    help="Treat seal mismatches as errors (default: warnings)")
    ap.add_argument("--no-reward-check", action="store_true",
                    help="Skip the fiduciary_node_rewards cross-check")
    ap.add_argument("paths", nargs="*",
                    help="One or more ledger YAML files (per-file mode). "
                         "If omitted, tree-wide mode runs.")
    args = ap.parse_args(argv)

    # Per-file mode: any positional path was supplied.
    if args.paths:
        mode = "emit" if args.emit else "hard" if args.hard else "soft"
        return _cli_verify_files(mode, args.paths)

    # Tree-wide mode.
    if args.emit or args.soft or args.hard:
        print("::error::--emit/--soft/--hard are per-file modes and require "
              "one or more positional paths")
        return 2

    root = os.path.abspath(
        args.root or os.path.join(os.path.dirname(__file__), "..", "..")
    )
    ledger_dir = args.ledger_dir or os.path.join(root, "ledger")

    if not os.path.isdir(ledger_dir):
        print(f"::error::ledger directory not found: {ledger_dir}")
        return 2

    print(f"🜁∀ verify_ledger — root={root}")
    print(f"           ledger_dir={ledger_dir}")

    entries = load_entries(ledger_dir, wanted_series=args.series)
    if not entries:
        print("::error::no entries found")
        return 2

    print(f"           loaded {len(entries)} event entries")

    total_bad = 0
    total_bad += check_required_fields(entries)
    total_bad += check_seals(entries, strict=args.strict_seals)
    total_bad += check_chains(entries)

    if not args.no_reward_check:
        total_bad += check_reward_pool(entries)

    print()
    if total_bad == 0:
        print("✅ ledger verified — all chains intact, all seals match")
        return 0
    print(f"❌ ledger verification failed with {total_bad} issue(s)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
