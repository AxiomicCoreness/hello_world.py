#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
# SPDX-License-Identifier: MIT
"""ledger_seal.py — the single seal-verification core for ledger/ and ledger.v2/.

Every seal regime the entries actually use lives here, and every verifier
(.github/scripts/verify_ledger.py, .github/scripts/verify_ledger_seals.py,
scripts/verify_ledger.py, tools/ledger_index.py) calls it, so they agree.

Regimes (all SHA3-256, FIPS 202):
  A        canonical JSON of body minus 'seal', sort_keys, (",", ":"),
           ensure_ascii=False, datetimes as ISO-8601 Z.
  A_ASCII  same as A but ensure_ascii=True (old scripts/verify_ledger.py form).
  B        GARDEN.EVENT.v1[.LEDGER] || 0x00 || "n|event|phi2=..|delta=..|theta=.."
           (domain .LEDGER for entry_index >= 9281; ASCII only).
  S        seal_sha3_256 convention (ledger/8973.yaml): canonical JSON,
           ensure_ascii=True, seal/seal_sha3_256/sha3_256/hash_sha3_256/hash
           excluded.

A seal that matches no regime is UNVERIFIED. It is never counted as a pass.
Stdlib only (YAML loading is the caller's job).
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import re
import uuid
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional

HASH_ALGO = "sha3_256"
HASH_RE = re.compile(r"([0-9a-fA-F]{64})")
EVENT_DOMAIN = b"GARDEN.EVENT.v1"
EVENT_DOMAIN_LEDGER = b"GARDEN.EVENT.v1.LEDGER"
PHI2 = "2.618033988749895"
DELTA = "b^2-4ac"
THETA = "2.5416018462"
REGIME_B_FROM = 9281
S_EXCLUDED_FIELDS = ("seal", "seal_sha3_256", "sha3_256", "hash_sha3_256", "hash")

VERIFIED = "verified"
UNVERIFIED = "unverified"
NO_SEAL = "no_declared_digest"


def json_default(obj: Any) -> Any:
    if isinstance(obj, _dt.datetime):
        if obj.tzinfo is None:
            return obj.strftime("%Y-%m-%dT%H:%M:%SZ")
        return obj.astimezone(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if isinstance(obj, (_dt.date, _dt.time)):
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


def _sha3(b: bytes) -> str:
    return hashlib.new(HASH_ALGO, b).hexdigest()


def regime_a(data: Dict[str, Any]) -> str:
    body = {k: v for k, v in data.items() if k != "seal"}
    return _sha3(json.dumps(body, sort_keys=True, separators=(",", ":"),
                            default=json_default, ensure_ascii=False).encode("utf-8"))


def regime_a_ascii(data: Dict[str, Any]) -> str:
    body = {k: v for k, v in data.items() if k != "seal"}
    return _sha3(json.dumps(body, sort_keys=True, separators=(",", ":"),
                            default=json_default).encode("utf-8"))


def regime_s(data: Dict[str, Any]) -> str:
    """seal_sha3_256 convention. Raises TypeError on non-JSON values, like before."""
    body = {k: v for k, v in data.items() if k not in S_EXCLUDED_FIELDS}
    return _sha3(json.dumps(body, sort_keys=True, separators=(",", ":"),
                            ensure_ascii=True).encode("utf-8"))


def regime_b(data: Dict[str, Any], n: Any = None) -> Optional[str]:
    if n is None:
        n = data.get("entry_index")
    event = data.get("event")
    if not isinstance(n, int) or isinstance(n, bool) or not isinstance(event, str):
        return None
    event = event.strip()
    domain = EVENT_DOMAIN_LEDGER if n >= REGIME_B_FROM else EVENT_DOMAIN
    payload = f"{n}|{event}|phi2={PHI2}|delta={DELTA}|theta={THETA}"
    try:
        pb = payload.encode("ascii")
    except UnicodeEncodeError:
        return None
    return _sha3(domain + b"\x00" + pb)


def declared_hex(data: Dict[str, Any]) -> Optional[str]:
    seal = str(data.get("seal", ""))
    m = HASH_RE.findall(seal)
    if m:
        return m[-1].lower()
    for key in ("terminal_hex", "witness_prefix", "verification_hash"):
        v = data.get(key)
        if isinstance(v, str) and HASH_RE.fullmatch(v.strip()):
            return v.strip().lower()
    return None


def declared_digests(data: Dict[str, Any]) -> List[str]:
    out: List[str] = []
    seal = data.get("seal", "")
    if isinstance(seal, str):
        s = seal.strip().lower()
        if HASH_RE.fullmatch(s):
            out.append(s)
        parts = s.split()
        if parts and HASH_RE.fullmatch(parts[-1]):
            out.append(parts[-1])
    d = declared_hex(data)
    if d:
        out.append(d)
    s = data.get("seal_sha3_256")
    if isinstance(s, str) and HASH_RE.fullmatch(s.strip()):
        out.append(s.strip().lower())
    return list(dict.fromkeys(out))


def seal_field_matches(data: Dict[str, Any], computed: Optional[str]) -> bool:
    return bool(computed) and computed.lower() in declared_digests(data)


def compute_all(data: Dict[str, Any], n: Any = None) -> Dict[str, Optional[str]]:
    out: Dict[str, Optional[str]] = {}
    for name, fn in (("A", regime_a), ("A_ASCII", regime_a_ascii), ("S", regime_s),
                     ("B", lambda d: regime_b(d, n))):
        try:
            out[name] = fn(data)
        except (TypeError, ValueError):  # uncomputable => cannot match, never a pass
            out[name] = None
    return out


def verify_entry(data: Dict[str, Any], n: Any = None) -> Dict[str, Any]:
    """Return {status, regimes, expected_regime, mismatch, declared}.

    status: verified | unverified | no_declared_digest. Never fails open.
    """
    if n is None:
        n = data.get("entry_index")
    declared = declared_digests(data)
    computed = compute_all(data, n)
    matched = [r for r, h in computed.items() if h and h in declared]
    # seal_sha3_256 declared => only regime S may satisfy it (explicit preimage).
    if "seal_sha3_256" in data and isinstance(data.get("seal_sha3_256"), str):
        want = data["seal_sha3_256"].strip().lower()
        if computed["S"] != want:
            # explicit preimage disagrees: hard unverified, as verify_ledger_seals.py
            return {"status": UNVERIFIED, "regimes": [], "expected_regime": None,
                    "regime_mismatch": False, "declared": declared,
                    "reason": "seal_sha3_256 mismatch"}
    expected = "B" if isinstance(n, int) and not isinstance(n, bool) and n >= REGIME_B_FROM else None
    if not declared:
        status = NO_SEAL
    elif matched:
        status = VERIFIED
    else:
        status = UNVERIFIED
    mismatch = bool(status == VERIFIED and expected and expected not in matched)
    return {"status": status, "regimes": matched, "expected_regime": expected,
            "regime_mismatch": mismatch, "declared": declared}
