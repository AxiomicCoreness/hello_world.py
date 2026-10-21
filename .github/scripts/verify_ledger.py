#!/usr/bin/env python3
"""
verify_ledger.py — verify a ledger entry's seal against its body.

HASH ALGORITHM: SHA3-256 (FIPS 202). Non-negotiable.

Dual regime (append-only safe):
  Regime A (89xx): SHA3-256(canonical JSON body minus 'seal')
  Regime B (92xx, and 9281+): SHA3-256(GARDEN.EVENT.v1[.LEDGER] || 0x00 || n|event|phi2|delta|theta)
                   For entry_index >= 9281 the domain is GARDEN.EVENT.v1.LEDGER;
                   earlier Regime B uses GARDEN.EVENT.v1. ASCII b^2 only — Unicode b² is rejected.

For entry_index >= 9281, Regime B is the expected regime. An A-only match
is accepted but flagged.
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
from typing import Any, Dict, Iterable, List, Optional

try:
    import yaml
    HAVE_YAML = True
except ImportError:
    HAVE_YAML = False

HASH_ALGO = "sha3_256"
HASH_RE = re.compile(r"([0-9a-fA-F]{64})")

EVENT_DOMAIN = b"GARDEN.EVENT.v1"
EVENT_DOMAIN_LEDGER = b"GARDEN.EVENT.v1.LEDGER"
PHI2 = "2.618033988749895"
DELTA = "b^2-4ac"
THETA = "2.5416018462"

NORTH_STAR_HZ = 71.975
PHASE_LOCK_DEG = 202.6
WORKLOAD = 0.0
COHERENCE = 1.0

REQUIRED_FIELDS = ("entry_index", "event", "seal", "witness_chain")
NON_EVENT_CLASSES = frozenset({"design-note", "policy", "index"})
KNOWN_SERIES_PREFIXES = ("83", "91", "92", "51", "00")

WITNESS_RE = re.compile(r"^\s*(\d{3,6})\s*[→>-]+\s*(\d{3,6})")
GENESIS_ANCHORS = {"0000"}
SERIES_ORIGINS = {"510510": "8980"}

# Allow floats with trailing zeros, stripping them cleanly
ENTRY_INDEX_RE = re.compile(r"^entry_index:\s*['\"]?(\d+)(?:\.\d*)?['\"]?", re.MULTILINE)
REGIME_B_FROM = 9281

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

class Entry:
    __slots__ = (
        "path", "index", "n", "series", "data",
        "seal_ok", "seal_computed",
        "chain_prev", "chain_next", "notes",
    )

    def __init__(self, path: str, index: str, series: str, data: Dict[str, Any],
                 n: Any = None):
        self.path = path
        self.index = index
        self.n = n if n is not None else data.get("entry_index")
        self.series = series
        self.data = data
        self.seal_ok: Optional[bool] = None
        self.seal_computed: Optional[str] = None
        self.chain_prev: Optional[str] = None
        self.chain_next: Optional[str] = None
        self.notes: List[str] = []

def _iter_yaml_files(ledger_dir: str) -> Iterable[str]:
    if not os.path.isdir(ledger_dir):
        return
    for name in sorted(os.listdir(ledger_dir)):
        if name.endswith((".yaml", ".yml")):
            yield os.path.join(ledger_dir, name)

def _load_yaml_file(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    if not HAVE_YAML:
        raise RuntimeError("PyYAML required to load ledger YAML files")
    docs = list(yaml.safe_load_all(text))
    return [d for d in docs if isinstance(d, dict) and d]

def resolve_entry_index(data: Dict[str, Any], raw_text: Optional[str] = None,
                        raw_match: Optional[str] = None) -> Any:
    if raw_match is None and raw_text is not None:
        m = ENTRY_INDEX_RE.search(raw_text)
        raw_match = m.group(1) if m else None
    if raw_match is not None:
        return int(raw_match)
    parsed = data.get("entry_index") if isinstance(data, dict) else None
    if isinstance(parsed, str) and parsed.strip().isdigit():
        return int(parsed.strip())
    if isinstance(parsed, float):
        return int(parsed)
    return parsed

def _index_str(n: Any) -> str:
    return str(n).zfill(4)

def _series_of(index: str) -> str:
    z = index.zfill(4)
    for p in KNOWN_SERIES_PREFIXES:
        if z.startswith(p):
            return p
    return z[:2]

def _is_non_event(doc: Dict[str, Any]) -> bool:
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
        with open(path, "r", encoding="utf-8") as f:
            raw_hits = ENTRY_INDEX_RE.findall(f.read())
        with_index = [d for d in docs if d.get("entry_index") is not None]
        raw_for = dict(zip(map(id, with_index), raw_hits)) \
            if len(raw_hits) == len(with_index) else {}
        for doc in docs:
            if _is_non_event(doc):
                continue
            raw_index = doc.get("entry_index")
            if raw_index is None:
                continue
            n = resolve_entry_index(doc, raw_match=raw_for.get(id(doc)))
            index = _index_str(n)
            series = _series_of(index)
            if wanted_series and series not in wanted_series:
                continue
            entries.append(Entry(path=path, index=index, series=series, data=doc, n=n))
    return entries

def canonical_hash(data: dict) -> str:
    body = {k: v for k, v in data.items() if k != "seal"}
    canon = json.dumps(
        body,
        sort_keys=True,
        separators=(",", ":"),
        default=json_default,
        ensure_ascii=False,
    )
    return hashlib.new(HASH_ALGO, canon.encode("utf-8")).hexdigest()

def event_hash(data: dict, n: Any = None) -> Optional[str]:
    if n is None:
        n = resolve_entry_index(data)
    event = data.get("event")
    if not isinstance(n, int) or isinstance(n, bool) or not isinstance(event, str):
        return None
    
    event = event.strip() # Defensive stripping of whitespace
    domain = EVENT_DOMAIN_LEDGER if n >= REGIME_B_FROM else EVENT_DOMAIN
    payload = f"{n}|{event}|phi2={PHI2}|delta={DELTA}|theta={THETA}"
    try:
        payload_bytes = payload.encode("ascii")
    except UnicodeEncodeError:
        return None
    return hashlib.new(
        HASH_ALGO, domain + b"\x00" + payload_bytes
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

def _emit_diagnostics(data: dict, declared: str,
                      computed_a: str, computed_b: Optional[str],
                      regime: Optional[str], idx: Any = None) -> None:
    print(f"   entry_index:  {idx if idx is not None else data.get('entry_index', '?')}")
    print(f"   declared:     {declared}")
    print(f"   computed_A:   {computed_a}")
    print(f"   computed_B:   {computed_b}")
    print(f"   regime:       {regime or 'MISMATCH'}")
    print(
        f"   north_star:   {NORTH_STAR_HZ} Hz · {PHASE_LOCK_DEG}° · "
        f"W={WORKLOAD} · C={COHERENCE}"
    )

SEALED_CONCRETE_FROM = 9286
_HEX64 = re.compile(r"^[0-9a-f]{64}$")

def _pending_fields(obj: Any, path: str = "") -> List[str]:
    found: List[str] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            found += _pending_fields(v, f"{path}.{k}" if path else str(k))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            found += _pending_fields(v, f"{path}[{i}]")
    elif isinstance(obj, str) and obj.strip().upper().startswith("PENDING"):
        found.append(path)
    return found

def sealed_concrete_violations(data: dict, n: Any = None) -> List[str]:
    idx = n if n is not None else resolve_entry_index(data)
    if str(data.get("status", "")).upper() != "SEALED":
        return []
    if not isinstance(idx, int) or idx < SEALED_CONCRETE_FROM:
        return []
    problems = []
    prev = data.get("prev_hash")
    if not (isinstance(prev, str) and _HEX64.match(prev)):
        problems.append(f"prev_hash not 64-hex: {prev!r}")
    problems += [f"unresolved field: {f}" for f in _pending_fields(data)]
    return problems

def verify(path: Path, mode: str) -> bool:
    if not path.exists():
        msg = f"⚠️ {path} not found"
        if mode == "hard":
            print(f"{msg} — hard fail")
            return False
        print(f"{msg} — soft skip")
        return True

    try:
        text = path.read_text(encoding="utf-8")
        data = yaml.safe_load(text) or {}
    except (yaml.YAMLError, ValueError) as e:
        print(f"❌ {path}: YAML parse error: {e}")
        return False if mode == "hard" else True

    if not isinstance(data, dict):
        print(f"❌ {path}: top-level YAML is not a mapping")
        return False if mode == "hard" else True

    if _is_non_event(data):
        print(f"— {path}: document_class={data.get('document_class') or data.get('kind')} — seal check skipped")
        return True

    idx = resolve_entry_index(data, text)
    problems = sealed_concrete_violations(data, idx)
    if problems:
        for pr in problems:
            print(f"❌ {path}: SEALED but not concrete ({pr})")
        if mode == "hard":
            return False

    declared = declared_hex(data)
    if not declared:
        print(f"❌ {path}: no 64-hex SHA3-256 digest in seal/terminal_hex")
        return False if mode == "hard" else True

    try:
        computed_a = canonical_hash(data)
        computed_b = event_hash(data, idx)
    except Exception as e:
        print(f"❌ {path}: canonicalisation failed: {e}")
        return False if mode == "hard" else True

    regime: Optional[str] = None
    if declared == computed_a:
        regime = "A(json)"
    elif computed_b is not None and declared == computed_b:
        regime = "B(event)"

    if isinstance(idx, int) and idx >= REGIME_B_FROM and regime == "A(json)":
        print(f"⚠️ {path}: entry {idx} matched Regime A only; Regime B expected for >= {REGIME_B_FROM}")

    if mode == "emit":
        print(f"— {path}")
        _emit_diagnostics(data, declared, computed_a, computed_b, regime, idx)
        return True

    if regime is None:
        print(f"❌ {path}: seal mismatch (sha3_256)")
        print(f"   declared:   {declared}")
        print(f"   computed_A: {computed_a}")
        if computed_b is not None:
            print(f"   computed_B: {computed_b}")
        return False if mode == "hard" else True

    entry_index = idx if idx is not None else "?"
    print(
        f"✅ {path}: sha3_256 seal verified "
        f"(entry_index={entry_index}, regime={regime}, {declared[:16]}...)"
    )
    return True

LOAD_ERRORS: List[str] = []

def check_required_fields(entries: List[Entry]) -> int:
    bad = 0
    for e in entries:
        missing = [f for f in REQUIRED_FIELDS if f not in e.data]
        if missing:
            print(f"::error file={e.path}::entry {e.index} missing fields: {missing}")
            bad += 1
    return bad

def seal_field_matches(data: Dict[str, Any], computed: str) -> bool:
    if not computed:
        return False
    computed = computed.lower()
    seal = data.get("seal", "")
    if isinstance(seal, str):
        if seal.lower() == computed:
            return True
        parts = seal.split()
        if parts and parts[-1].lower() == computed:
            return True
    d = declared_hex(data)
    if d and d == computed:
        return True
    s = data.get("seal_sha3_256")
    if isinstance(s, str) and s.strip().lower() == computed:
        return True
    return False

def entry_declared_digest(data: Dict[str, Any]) -> Optional[str]:
    s = data.get("seal_sha3_256")
    if isinstance(s, str) and HASH_RE.fullmatch(s.strip()):
        return s.strip().lower()
    return declared_hex(data)

def check_seals(entries: List[Entry], strict: bool = False) -> int:
    bad = 0
    for e in entries:
        computed_a = canonical_hash(e.data)
        computed_b = event_hash(e.data, e.n)
        ok_a = seal_field_matches(e.data, computed_a)
        ok_b = computed_b is not None and seal_field_matches(e.data, computed_b)
        ok = ok_a or ok_b
        e.seal_computed = computed_b if ok_b else computed_a
        e.seal_ok = ok
        idx = e.n
        if ok_a and not ok_b and isinstance(idx, int) and idx >= REGIME_B_FROM:
            print(f"::warning file={e.path}::entry {e.index} matched Regime A only; "
                  f"Regime B expected for >= {REGIME_B_FROM}")
        if not ok:
            bad += 1
            level = "error" if strict else "warning"
            print(f"::{level} file={e.path}::entry {e.index} seal mismatch")
            print(f"        computed_A:      {computed_a}")
            print(f"        computed_B:      {computed_b}")
            print(f"        seal field:      {e.data.get('seal')}")
            if "seal_sha3_256" in e.data:
                print(f"        seal_sha3_256:   {e.data.get('seal_sha3_256')}")
    return bad

def _weld_anchor(root: str, prev_index: str) -> Optional[str]:
    for ext in (".yaml", ".yml"):
        p = os.path.join(root, "ledger", prev_index + ext)
        if os.path.isfile(p):
            try:
                docs = _load_yaml_file(p)
                with open(p, "r", encoding="utf-8") as f:
                    text = f.read()
            except Exception:
                return None
            for d in docs:
                n = resolve_entry_index(d, text if len(docs) == 1 else None)
                if n is not None and _index_str(n) == prev_index:
                    return entry_declared_digest(d)
    return None

def check_chains(entries: List[Entry], weld_root: Optional[str] = None) -> int:
    by_series: Dict[str, List[Entry]] = {}
    by_index: Dict[str, Entry] = {}
    for e in entries:
        by_series.setdefault(e.series, []).append(e)
        by_index.setdefault(e.index, e)

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
                if prev_entry.chain_next != e.index and prev != prev_entry.index:
                    print(f"::error file={e.path}::entry {e.index} "
                          f"previous series entry {prev_entry.index} "
                          f"points at {prev_entry.chain_next}, expected {e.index}")
                    bad += 1

            if e.index not in GENESIS_ANCHORS and i == 0 and prev not in GENESIS_ANCHORS:
                if weld_root is not None:
                    anchor = _weld_anchor(weld_root, prev)
                    ph = str(e.data.get("prev_hash", "")).strip().lower()
                    if anchor and ph == anchor:
                        print(f"   weld: {e.index} <- ledger/{prev} ({anchor[:16]}...)")
                        continue
                    print(f"::error file={e.path}::entry {e.index} weld to ledger/{prev} "
                          f"failed: prev_hash={ph or None} anchor={anchor}")
                    bad += 1
                else:
                    pred = by_index.get(prev) if SERIES_ORIGINS.get(e.index) == prev else None
                    succ = pred.data.get("successor") if pred is not None else None
                    if pred is not None and (succ is None or _index_str(succ) == e.index):
                        print(f"   origin: {e.index} <- {prev} (series {series} origin)")
                        continue
                    print(f"::error file={e.path}::entry {e.index} "
                          f"first in series but prev {prev} is not a genesis anchor")
                    bad += 1

    return bad

def _is_verified_mirror(root: str, e: "Entry", flat_path: str) -> bool:
    m = e.data.get("mirrors")
    if not isinstance(m, dict) or e.data.get("supersedes", "none") != "none":
        return False
    f, want = m.get("file"), str(m.get("sha3_256", "")).lower()
    if not isinstance(f, str) or os.path.normpath(os.path.join(root, f)) != os.path.normpath(flat_path):
        return False
    try:
        raw = Path(flat_path).read_bytes()
    except OSError:
        return False
    return hashlib.new(HASH_ALGO, raw).hexdigest() == want

def check_cross_root_duplicates(root: str) -> int:
    a = load_entries(os.path.join(root, "ledger"))
    b = load_entries(os.path.join(root, "ledger.v2"))
    if not b:
        return 0
    flat = {e.index: e.path for e in a}
    bad = 0
    for e in b:
        if e.index in flat:
            if _is_verified_mirror(root, e, flat[e.index]):
                print(f"   mirror: {e.path} mirrors {flat[e.index]} (sha3_256 of v1 bytes matches)")
                continue
            print(f"::error file={e.path}::entry {e.index} duplicates {flat[e.index]}")
            bad += 1
    print(f"── cross-root: ledger/={len(a)} ledger.v2/={len(b)} duplicates={bad}")
    return bad

def main() -> int:
    ap = argparse.ArgumentParser(description="Verify ledger seals and chains.")
    ap.add_argument("files", nargs="*", help="YAML files to verify")
    ap.add_argument("--hard", action="store_true", help="fail on mismatch")
    ap.add_argument("--soft", action="store_true", help="warn on mismatch (default)")
    ap.add_argument("--emit", action="store_true", help="print digests, never fail")
    ap.add_argument("--root", default=".", help="repo root")
    ap.add_argument("--ledger-dir", default="ledger",
                    help="ledger directory relative to --root (ledger or ledger.v2)")
    ap.add_argument("--series", action="append", help="limit to series prefix")
    ap.add_argument("--strict-seals", action="store_true",
                    help="tree mode: seal mismatches are errors and fail the run")
    ap.add_argument("--no-reward-check", action="store_true",
                    help="accepted for workflow compatibility; no reward check exists")
    ap.add_argument("--mode", choices=["soft", "hard", "emit"], default="soft",
                    help="explicit mode; overrides --hard/--soft/--emit (default: soft)")
    args = ap.parse_args()

    missing = [f for f in args.files if not os.path.isfile(f)]
    if missing:
        for f in missing:
            print(f"::error::missing path: {f}")
        return 2

    ap_mode = getattr(args, "mode", None)
    mode = ap_mode or ("emit" if args.emit else ("hard" if args.hard else "soft"))

    if args.files:
        ok = True
        for f in args.files:
            ok = verify(Path(f), mode) and ok
        return 0 if ok else 1

    ledger_dir = os.path.join(args.root, args.ledger_dir)
    is_v2 = os.path.basename(os.path.normpath(args.ledger_dir)) == "ledger.v2"
    entries = load_entries(ledger_dir, args.series)
    print(f"loaded {len(entries)} entries from {ledger_dir}")
    strict = mode == "hard" or args.strict_seals
    bad = len(LOAD_ERRORS)
    bad += check_required_fields(entries)
    bad += check_seals(entries, strict=strict)
    bad += check_chains(entries, weld_root=args.root if is_v2 else None)
    bad += check_cross_root_duplicates(args.root)
    print(f"bad: {bad}")
    return 0 if bad == 0 else (1 if strict else 0)

if __name__ == "__main__":
    raise SystemExit(main())
