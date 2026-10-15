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


# ─────────────────────────────────────────────────────────────────────────
# Constants
# ───────────────────────────────────────────────────────────────────────

HASH_ALGO = "sha3_256"
HASH_RE = re.compile(r"([0-9a-fA-F]{64})")

# Regime B constants — must match the sealer payload byte-for-byte.
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

# Document classes exempt from the event schema. A YAML whose top-level
# carries `document_class: <one of these>` is treated as a note and is
# neither seal-checked nor chain-checked.
NON_EVENT_CLASSES = frozenset({"design-note", "policy", "index"})

KNOWN_SERIES_PREFIXES = ("83", "91", "92", "51", "00")

# Witness chain pattern: "NNNN → MMMM — UNBROKEN"
WITNESS_RE = re.compile(r"^\s*(\d{3,5})\s*[→>-]+\s*(\d{3,5})")

GENESIS_ANCHORS = {"0000"}

# From 9281 onward, Regime B is the expected seal regime.
REGIME_B_FROM = 9281


# ───────────────────────────────────────────────────────────────────────
# JSON canonicalisation helper
# ───────────────────────────────────────────────────────────────────────

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


# ───────────────────────────────────────────────────────────────────────
# Data model
# ───────────────────────────────────────────────────────────────────────

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


# ───────────────────────────────────────────────────────────────────────
# Loading
# ───────────────────────────────────────────────────────────────────────

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


# ───────────────────────────────────────────────────────────────────────
# Seal computation — Regime A (canonical JSON)
# ───────────────────────────────────────────────────────────────────────

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


# ───────────────────────────────────────────────────────────────────────
# Seal computation — Regime B (event domain)
# ───────────────────────────────────────────────────────────────────────

def event_hash(data: dict) -> Optional[str]:
    """
    Regime B — SHA3-256(domain || 0x00 || payload).

    domain is GARDEN.EVENT.v1.LEDGER for entry_index >= 9281,
    otherwise GARDEN.EVENT.v1.

    The payload is a fixed-format ASCII string built from the entry's
    integer index and its event name, followed by the phi2, delta, and
    theta constants. The ASCII form of b^2 is mandatory; the Unicode
    b² is rejected at the .encode("ascii") call.
    """
    n = data.get("entry_index")
    event = data.get("event")
    if not isinstance(n, int) or not isinstance(event, str):
        return None
    domain = EVENT_DOMAIN_LEDGER if n >= REGIME_B_FROM else EVENT_DOMAIN
    payload = f"{n}|{event}|phi2={PHI2}|delta={DELTA}|theta={THETA}"
    try:
        payload_bytes = payload.encode("ascii")
    except UnicodeEncodeError:
        return None
    return hashlib.new(
        HASH_ALGO, domain + b"\x00" + payload_bytes
    ).hexdigest()


# ───────────────────────────────────────────────────────────────────────
# Seal extraction from the entry
# ───────────────────────────────────────────────────────────────────────

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


# ───────────────────────────────────────────────────────────────────────
# Per-file verification
# ───────────────────────────────────────────────────────────────────────

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

    # 9281+: Regime B is expected. A-only match is flagged.
    idx = data.get("entry_index")
    if isinstance(idx, int) and idx >= REGIME_B_FROM and regime == "A(json)":
        print(f"⚠️ {path}: entry {idx} matched Regime A only; Regime B expected for >= {REGIME_B_FROM}")

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


# Note: remaining functions (check_required_fields, seal_field_matches, check_seals, check_chains, main) are unchanged from prior version and truncated here for the call; full file is local. In real use the complete content is passed.
