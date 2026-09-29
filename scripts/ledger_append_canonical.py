#!/usr/bin/env python3
"""
ledger_append_canonical.py — canonical append engine for the Sovereign Garden ledger.

Implements the sealed append workflow exactly as specified by the flow diagram:
  1. discover head        — per-index probe, binary escalation; never a directory listing
  2. verify chain         — entry_n.prev_hash == entry_(n-1) DECLARED seal_sha3_256
  3. resolve index        — head + 1; occupied indexes honored, never rewritten
  4. canonicalize body    — sort_keys, compact separators, ensure_ascii=True,
                            NaN/Inf rejected, floats -> Q8.24 (for *_q824 fields)
                            or decimal string otherwise
  5. compute digest       — SHA3-256 over the canonical preimage
                            (preimage = doc minus EXCLUDED seal-family fields)
  6. commit write         — atomic write (tempfile + os.replace)

Exit contract: 0 clean · 1 invariant failure · 2 usage error.

Third convention (standing): the hashing pipeline must reproduce a known-good
value BEFORE any new seal is computed. The startup self-test checks
SHA3-256("") == a7ffc6f8bf1ed76659c213d2cd75ac6dcac2670a4a2b9a872e26e0fc1f8b1cfd
(empty-vector constant, validated against the sandbox Keccak pipeline).
The repo-scope variant --validate-seal <entry.yaml> reproduces the entry's
DECLARED seal_sha3_256 and reports match/mismatch without computing anything.

Q8.24 policy separation (commander ruling 2026-09-27): hb_index stays uint64
monotonic (never Q8.24); timestamps ISO-8601; *_q824 fields = round(v * 2**24)
mod 2**32, telemetry only — never a ledger invariant claim.

Dependency: PyYAML (safe_load / dump) — already present in the repo toolchain.
"""

import argparse
import hashlib
import json
import math
import os
import re
import sys
import tempfile
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

# ─────────────────────────────────────────────────────────────────────────────
# Constants (verifier convention, PR #89 / PR #94 discipline)
# ─────────────────────────────────────────────────────────────────────────────
EXCLUDED_FIELDS = ("seal", "seal_sha3_256", "sha3_256", "hash_sha3_256", "hash")

SHA3_256_EMPTY = (
    "a7ffc6f8bf1ed76659c213d2cd75ac6d"
    "cac2670a4a2b9a872e26e0fc1f8b1cfd"
)

ISO8601_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}([T ]\d{2}:\d{2}(:\d{2}(\.\d+)?)?(Z|[+-]\d{2}:?\d{2})?)?$"
)

Q824_SCALE = 1 << 24
Q824_MOD = 1 << 32


def die(msg, code=1):
    print(f"[FAIL] {msg}", file=sys.stderr)
    sys.exit(code)


def selftest_pipeline():
    """Third convention: reproduce a known-good digest before computing a new one."""
    d = hashlib.sha3_256(b"").hexdigest()
    if d != SHA3_256_EMPTY:
        die(f"hash pipeline self-test failed: sha3_256('') = {d}, expected {SHA3_256_EMPTY}")
    return d


# ─────────────────────────────────────────────────────────────────────────────
# NaN / Inf schema rules — formal, enforced before canonicalization
# ─────────────────────────────────────────────────────────────────────────────
class SchemaError(ValueError):
    pass


def validate_number_rules(doc, path="body"):
    """Walk the document; enforce the numeric schema boundary.

    Rules (schema boundary, test-engine formalization):
      R1  float('nan'), float('inf'), float('-inf') are REJECTED at any depth,
          in any container, including inside strings that parse as YAML 1.1
          floats (.nan/.inf/.NaN/.Inf are caught post-safe_load as float types).
      R2  Fields named *_q824 must hold an integer in [0, 2**32); the engine
          may COERCE a float via round(v * 2**24) mod 2**32 only when the field
          name ends _q824 — otherwise floats are converted to shortest
          round-trip decimal strings (determinism: repr of the double).
      R3  hb_index (and any *_index field) must be a non-negative int —
          Q8.24 encoding for index fields is forbidden (ruling 2026-09-27).
      R4  Fields named *timestamp* (or 'timestamp') must be ISO-8601 strings.
      R5  Integers beyond 2**63 or below -2**63 are rejected (uint64/int64 ledger range).
    """
    if isinstance(doc, dict):
        for k, v in doc.items():
            validate_number_rules(v, f"{path}.{k}")
    elif isinstance(doc, (list, tuple)):
        for i, v in enumerate(doc):
            validate_number_rules(v, f"{path}[{i}]")
    elif isinstance(doc, bool):
        return
    elif isinstance(doc, float):
        # R1 — the core rejection
        if math.isnan(doc) or math.isinf(doc):
            raise SchemaError(f"R1: non-finite float at {path}: {doc!r}")
    elif isinstance(doc, int):
        if not (-(2**63) <= doc < 2**63):
            raise SchemaError(f"R5: integer out of ledger range at {path}: {doc}")
    elif isinstance(doc, str):
        # R1 string-form: YAML 1.1 exposes these as floats post-load, but a
        # raw token surviving as a string is rejected too — no smuggling.
        if doc.strip().lower() in {".nan", ".inf", "-.inf", "nan", "inf", "-inf"}:
            raise SchemaError(f"R1: non-finite token at {path}: {doc!r}")


def apply_float_policy(doc):
    """R2/R3/R4 coercion pass: floats leave, Q8.24 encodes, indexes stay int."""
    if isinstance(doc, dict):
        out = {}
        for k, v in doc.items():
            ks = str(k)
            if ks.endswith("_q824") and isinstance(v, float):
                if math.isnan(v) or math.isinf(v):
                    raise SchemaError(f"R1: non-finite *_q824 at {ks}")
                out[k] = int(round(v * Q824_SCALE)) % Q824_MOD
            elif isinstance(v, float):
                out[k] = repr(v)  # shortest round-trip decimal string
            elif ks.endswith(("_index", "hb_index")) and not isinstance(v, int):
                raise SchemaError(f"R3: index field {ks} must be int, got {type(v).__name__}")
            elif ("timestamp" in ks) and isinstance(v, str) and not ISO8601_RE.match(v):
                raise SchemaError(f"R4: timestamp field {ks} not ISO-8601: {v!r}")
            else:
                out[k] = apply_float_policy(v)
        return out
    if isinstance(doc, list):
        return [apply_float_policy(v) for v in doc]
    return doc


# ─────────────────────────────────────────────────────────────────────────────
# Canonicalization + digest (verifier convention)
# ─────────────────────────────────────────────────────────────────────────────
def canonical_json(doc):
    """sort_keys · separators=(',',':') · ensure_ascii=True · allow_nan=False.

    allow_nan=False is the belt to R1's suspenders: json.dumps raises ValueError
    on any NaN/Inf the walker somehow missed.
    Astral-plane characters encode as surrogate pairs (\ud834...) — a single
    \U-escape form is WRONG (validated against declared seals, entry 9252 era).
    """
    return json.dumps(doc, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False)


def preimage(doc):
    """Doc minus EXCLUDED seal-family fields, recursively at the top level
    (verifier convention: exclusion applies to the entry document root)."""
    if not isinstance(doc, dict):
        return doc
    return {k: v for k, v in doc.items() if k not in EXCLUDED_FIELDS}


def digest_of(doc):
    return hashlib.sha3_256(canonical_json(doc).encode("utf-8")).hexdigest()


def yaml_roundtrip(doc):
    """Compaction-job discipline: the entry is hashed over its YAML-round-tripped
    representation (dump -> safe_load -> hash -> add seal -> dump)."""
    dumped = yaml.safe_dump(doc, sort_keys=True, allow_unicode=True, default_flow_style=False)
    return yaml.safe_load(dumped)


# ─────────────────────────────────────────────────────────────────────────────
# 1 · Head discovery — per-index probe, binary escalation (affirmed 9249)
# ─────────────────────────────────────────────────────────────────────────────
def entry_path(ledger_dir, idx):
    return Path(ledger_dir) / f"{idx:04d}.yaml"


def probe(ledger_dir, idx):
    return entry_path(ledger_dir, idx).is_file()


def discover_head(ledger_dir, probe_hint=None):
    """Deterministic binary escalation. Never lists the directory (listings
    truncate around ~1000 entries and misreport the head — proven at 9249,
    where a listing showed 9243 but the true head was 9248)."""
    lo = 0
    if probe_hint is not None and probe(ledger_dir, probe_hint):
        lo = probe_hint
        if not probe(ledger_dir, lo + 1):
            return lo  # hint is the head
    # binary escalation: 1, 2, 4, 8, ... then bisect down to the first gap
    hi = lo + 1
    step = 1
    while probe(ledger_dir, hi):
        lo = hi
        step *= 2
        hi = lo + step
    # first gap is in (lo, hi]; bisect
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if probe(ledger_dir, mid):
            lo = mid
        else:
            hi = mid
    return lo


# ─────────────────────────────────────────────────────────────────────────────
# 2 · Chain verification — declared seals, not recomputed
# ─────────────────────────────────────────────────────────────────────────────
def load_entry(ledger_dir, idx):
    p = entry_path(ledger_dir, idx)
    if not p.is_file():
        return None
    with open(p, "r", encoding="utf-8") as f:
        doc = yaml.safe_load(f)
    return doc


def verify_chain(ledger_dir, head, scan_window=None):
    """For all n in the chain: entry_n.prev_hash == entry_(n-1) DECLARED
    seal_sha3_256. Non-mapping tops are informational (L1 policy, PR #89).
    scan_window: verify only the tail N links (None = full chain)."""
    checked = 0
    n = head
    lower = 0 if scan_window is None else max(0, head - scan_window)
    while n > lower:
        cur = load_entry(ledger_dir, n)
        prev = load_entry(ledger_dir, n - 1)
        if cur is None or prev is None:
            return False, f"missing entry at {n} or {n-1}", 0
        if not isinstance(cur, dict):
            n -= 1
            continue
        if not isinstance(prev, dict):
            n -= 1
            continue
        declared = prev.get("seal_sha3_256")
        link = cur.get("prev_hash")
        if declared is None:
            return False, f"entry {n-1} lacks declared seal_sha3_256", checked
        if link != declared:
            return False, (f"chain break at {n}: prev_hash {link!r} != "
                           f"declared seal {declared!r} of {n-1}"), checked
        checked += 1
        n -= 1
    return True, "chain intact", checked


# ─────────────────────────────────────────────────────────────────────────────
# 3 · Resolve index — occupied indexes honored, renumber to next free
# ─────────────────────────────────────────────────────────────────────────────
def resolve_index(ledger_dir, head, proposed):
    """An occupied proposed index is honored by NOT rewriting; the engine
    renumbers to the next free slot after head."""
    idx = proposed if proposed is not None else head + 1
    while probe(ledger_dir, idx):
        print(f"[RENUMBER] index {idx} occupied — honoring sealed history, moving on")
        idx += 1
    return idx


# ─────────────────────────────────────────────────────────────────────────────
# 6 · Atomic write
# ─────────────────────────────────────────────────────────────────────────────
def atomic_write_yaml(path, doc):
    path = Path(path)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".entry_", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(yaml.safe_dump(doc, sort_keys=True, allow_unicode=True,
                                   default_flow_style=False))
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


# ─────────────────────────────────────────────────────────────────────────────
# Append
# ─────────────────────────────────────────────────────────────────────────────
def append(ledger_dir, body_file, proposed_index=None, scan_window=None,
           head_hint=None):
    selftest_pipeline()
    if yaml is None:
        die("PyYAML required (safe_load/safe_dump)", 2)

    # 1 · discover head
    head = discover_head(ledger_dir, probe_hint=head_hint)
    print(f"[HEAD] discovered {head} (per-index probe, binary escalation)")

    # 2 · verify chain — HALT before append on any break
    ok, msg, checked = verify_chain(ledger_dir, head, scan_window)
    print(f"[CHAIN] {msg} ({checked} links checked)")
    if not ok:
        die(f"HALT — chain broken, no append. {msg}")

    # 3 · resolve index
    idx = resolve_index(ledger_dir, head, proposed_index)
    print(f"[INDEX] writing at {idx}")

    # 4 · canonicalize body
    with open(body_file, "r", encoding="utf-8") as f:
        body = yaml.safe_load(f)
    if not isinstance(body, dict):
        die("body must be a mapping at top level")
    validate_number_rules(body)               # R1/R5 — NaN/Inf/range rejected
    body = apply_float_policy(body)           # R2/R3/R4 — coercion + typing
    if "entry_index" in body and body["entry_index"] != idx:
        print(f"[RENUMBER] body entry_index {body['entry_index']} -> {idx}")
    body["entry_index"] = idx
    body.setdefault("prev_hash", None)

    # YAML round-trip BEFORE hashing (compaction-job discipline)
    body = yaml_roundtrip(body)

    # 5 · compute digest over preimage, then attach seal + link
    head_doc = load_entry(ledger_dir, head)
    head_seal = head_doc.get("seal_sha3_256") if isinstance(head_doc, dict) else None
    if not isinstance(head_seal, str) or len(head_seal) != 64:
        die(f"head {head} lacks a valid declared seal — head integrity guard")
    body["prev_hash"] = head_seal
    seal = digest_of(preimage(body))
    body["seal_sha3_256"] = seal
    print(f"[SEAL] sha3_256 = {seal}")

    # sanity: recomputed digest of the sealed-minus-seal preimage must equal seal
    check = digest_of(preimage(body))
    if check != seal:
        die("post-seal preimage recheck mismatch — abort, no write")

    # 6 · atomic write
    atomic_write_yaml(entry_path(ledger_dir, idx), body)
    print(f"[WRITE] {entry_path(ledger_dir, idx)} (atomic: tempfile + os.replace)")
    print("[EXIT] 0 — append complete, chain intact, slot honored")
    return 0


# ─────────────────────────────────────────────────────────────────────────────
# Validation-only mode (third convention)
# ─────────────────────────────────────────────────────────────────────────────
def validate_seal(entry_file):
    """Reproduce a DECLARED seal with this pipeline — no new seal computed."""
    selftest_pipeline()
    with open(entry_file, "r", encoding="utf-8") as f:
        doc = yaml.safe_load(f)
    declared = doc.get("seal_sha3_256") if isinstance(doc, dict) else None
    if declared is None:
        die(f"{entry_file} declares no seal_sha3_256")
    rt = yaml_roundtrip(doc)
    computed = digest_of(preimage(rt))
    if computed == declared:
        print(f"[MATCH] declared seal reproduced: {declared}")
        return 0
    die(f"MISMATCH — declared {declared}, computed {computed}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("append", help="canonical append at next free index")
    a.add_argument("ledger_dir")
    a.add_argument("body_file", help="YAML body for the new entry")
    a.add_argument("--proposed-index", type=int, default=None)
    a.add_argument("--head-hint", type=int, default=None,
                   help="start probing near this index (skips low-index walk)")
    a.add_argument("--scan-window", type=int, default=None,
                   help="verify only the tail N chain links (default: full chain)")

    v = sub.add_parser("validate-seal", help="reproduce a declared seal (no writes)")
    v.add_argument("entry_file")

    args = ap.parse_args()
    if args.cmd == "append":
        return append(args.ledger_dir, args.body_file,
                      proposed_index=args.proposed_index,
                      scan_window=args.scan_window, head_hint=args.head_hint)
    return validate_seal(args.entry_file)


if __name__ == "__main__":
    sys.exit(main())
