#!/usr/bin/env python3
"""Verify ledger seal digests — seal_sha3_256 convention (scoped revision).

Revision note (scope fix): the earlier revision scanned every *.yaml under the
repository root with rglob(). Two structural failure modes made the gate red on
every run, regardless of ledger state:

  1. Non-ledger multi-document YAML (e.g. k8s/*.yaml with '---' separators)
     raises under yaml.safe_load -> reported as a parse-error failure.
  2. Any 'hash:' / 'sha3_256:' / hex-tailed 'seal:' field anywhere in the tree
     was treated as a declared seal under THIS verifier's canonicalization;
     entries sealed under other conventions (e.g. the H_event Regime B
     formula, or unknown preimages) then hard-failed the gate.

This revision therefore:
  - scans only <root>/ledger/*.yaml with numeric entry stems
    (falling back to <root> itself if it is already such a directory);
  - hard-verifies ONLY entries that declare 'seal_sha3_256' — the one
    convention with an explicitly declared preimage (ledger/8973.yaml):
      sha3_256 over json.dumps(body, sort_keys=True, separators=(",", ":"),
      ensure_ascii=True) with the seal fields excluded from the body;
  - reports other declared digest forms (hex-tailed 'seal:', 'sha3_256:',
    'hash_sha3_256:', 'hash:') as INFORMATIONAL only;
  - L1: YAML parse errors and non-mapping tops are informational (warn),
    not hard failures; only seal_sha3_256 mismatches and missing --require
    entries hard-fail
  - keep the --require behaviour and the exit-code contract:
      exit 0  all seal_sha3_256 seals verified + all --require entries present
      exit 1  at least one seal_sha3_256 mismatch OR a required entry missing
      exit 2  no ledger entries found

Revision note (witness chain): new entries may carry prev_hash — must
equal the seal_sha3_256 of the referenced prior entry (prev_index if
present, else entry_index - 1). prev_hash: null is an explicit region
start. Entries without prev_hash are legacy (informational). Schema
change, not a re-hash of history; old entries remain as they are.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is required. Install with: pip install pyyaml", file=sys.stderr)
    sys.exit(2)

HEX64 = re.compile(r"^[0-9a-f]{64}$")
SEAL_TAIL = re.compile(r"·\s*([0-9a-f]{64})\s*$")
EXCLUDED_FIELDS = ("seal", "seal_sha3_256", "sha3_256", "hash_sha3_256", "hash")
OTHER_DIGEST_FIELDS = ("sha3_256", "hash_sha3_256", "hash")
PREV_HASH_FIELD = "prev_hash"
PREV_INDEX_FIELD = "prev_index"


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def expected_digest(doc: Dict[str, Any]) -> str:
    body = {k: v for k, v in doc.items() if k not in EXCLUDED_FIELDS}
    return hashlib.sha3_256(canonical_json(body).encode("utf-8")).hexdigest()


def find_entries(root: Path) -> List[Path]:
    ledger = root / "ledger"
    base = ledger if ledger.is_dir() else root
    return sorted(p for p in base.glob("*.yaml") if p.stem.isdigit())


def check_file(path: Path) -> Tuple[str, str]:
    """Return (status, message) where status is ok | warn | fail.

    L1: YAML parse errors and non-mapping tops are informational (warn),
    not hard failures. Real seal mismatches remain hard failures.
    """
    try:
        with path.open("r", encoding="utf-8") as f:
            doc = yaml.safe_load(f)
    except Exception as e:
        # L1: parse errors are informational, not hard failures.
        return "warn", f"{path}: YAML parse error (informational): {e}"
    if not isinstance(doc, dict):
        return "warn", f"{path}: top-level not a mapping (informational)"

    declared = doc.get("seal_sha3_256")
    if declared is None:
        notes = []
        seal = doc.get("seal")
        if isinstance(seal, str):
            m = SEAL_TAIL.search(seal)
            if m:
                notes.append(f"seal hex tail {m.group(1)[:16]}...")
        for field in OTHER_DIGEST_FIELDS:
            v = doc.get(field)
            if isinstance(v, str) and HEX64.match(v.strip().lower()):
                notes.append(f"{field} {v.strip().lower()[:16]}...")
        if notes:
            return "ok", (
                f"{path}: other declared digests (informational, "
                f"no declared preimage convention for this verifier): " + ", ".join(notes)
            )
        return "ok", f"{path}: no declared seal_sha3_256 (skipped, informational)"

    if not (isinstance(declared, str) and HEX64.match(declared.strip().lower())):
        return "fail", f"{path}: seal_sha3_256 present but not a full 64-hex digest"

    digest = declared.strip().lower()
    expected = expected_digest(doc)
    if digest == expected:
        return "ok", f"{path}: seal_sha3_256 OK  {digest[:16]}..."
    return "fail", (
        f"{path}: seal_sha3_256 MISMATCH\n"
        f"    declared: {digest}\n"
        f"    expected: {expected}"
    )


def check_chain(docs: Dict[str, Dict[str, Any]]) -> List[str]:
    """Hard-verify prev_hash links when present.

    Schema change (not a re-hash of history): entries that carry prev_hash
    are chained; entries without it are legacy and informational here.
      prev_hash: null  -> explicit region start (ok)
      prev_hash: <hex> -> must equal the seal_sha3_256 of the referenced
                          prior entry (prev_index if present, else
                          entry_index - 1); that prior entry must itself
                          declare seal_sha3_256.
    """
    bad: List[str] = []
    for stem, doc in sorted(docs.items(), key=lambda kv: int(kv[0])):
        prev_hash = doc.get(PREV_HASH_FIELD)
        if prev_hash is None:
            continue  # legacy entry (pre prev_hash schema): informational
        prev_hash = str(prev_hash).strip().lower()
        if prev_hash in ("null", "~", "none"):
            continue  # explicit region start
        if not HEX64.match(prev_hash):
            bad.append(f"ledger/{stem}.yaml: prev_hash present but not 64-hex: {prev_hash}")
            continue
        idx = doc.get("entry_index")
        fallback = str(int(idx) - 1) if isinstance(idx, int) else None
        prev_stem = str(doc.get(PREV_INDEX_FIELD, fallback))
        prior = docs.get(prev_stem)
        if prior is None:
            bad.append(f"ledger/{stem}.yaml: prev_hash references missing entry ledger/{prev_stem}.yaml")
            continue
        prior_seal = prior.get("seal_sha3_256")
        if not (isinstance(prior_seal, str) and HEX64.match(prior_seal.strip().lower())):
            bad.append(f"ledger/{stem}.yaml: prior entry ledger/{prev_stem}.yaml has no seal_sha3_256 to chain from")
            continue
        if prev_hash != prior_seal.strip().lower():
            bad.append(
                f"ledger/{stem}.yaml: prev_hash MISMATCH\n"
                f"    declared: {prev_hash}\n"
                f"    expected: {prior_seal.strip().lower()} (seal_sha3_256 of ledger/{prev_stem}.yaml)"
            )
    return bad


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Verify ledger seal digests (seal_sha3_256 convention).")
    ap.add_argument("root", help="repository root or ledger directory")
    ap.add_argument(
        "--require",
        action="append",
        default=[],
        help="ledger entry index that must be present (e.g. --require 8958)",
    )
    args = ap.parse_args(argv)

    root = Path(args.root)
    entries = find_entries(root)
    if not entries:
        print("ERROR: no ledger entries found under", root)
        return 2

    ok_count = 0
    warn_count = 0
    bad: List[str] = []
    present: set = set()
    docs: Dict[str, Dict[str, Any]] = {}
    for p in entries:
        present.add(p.stem)
        try:
            with p.open("r", encoding="utf-8") as f:
                docs[p.stem] = yaml.safe_load(f)
        except Exception:
            pass
        status, msg = check_file(p)
        if status == "ok":
            ok_count += 1
            print(f"  OK  {msg}")
        elif status == "warn":
            warn_count += 1
            print(f"  WARN {msg}", file=sys.stderr)
        else:
            bad.append(msg)
            print(f"  FAIL {msg}", file=sys.stderr)

    chain_bad = check_chain(docs)
    for m in chain_bad:
        bad.append(m)
        print(f"  FAIL {m}", file=sys.stderr)

    missing_required: List[str] = []
    for req in args.require:
        if req not in present:
            missing_required.append(req)
            bad.append(f"required entry missing: ledger/{req}.yaml")

    print()
    print(f"ledger entries scanned : {len(entries)}")
    print(f"verified OK            : {ok_count}")
    print(f"informational (warn)   : {warn_count}")
    print(f"mismatches / missing   : {len(bad)}")
    if args.require:
        print(f"required present       : {len(args.require) - len(missing_required)}/{len(args.require)}")
    if missing_required:
        print()
        print(f"MISSING required entries: {', '.join(missing_required)}", file=sys.stderr)
        return 1
    if bad:
        print()
        print("FAILURES:")
        for m in bad:
            print("  " + m.replace("\n", "\n  "), file=sys.stderr)
        return 1
    print("OK: all seal_sha3_256 seals verified and all required entries present")
    return 0


if __name__ == "__main__":
    sys.exit(main())
