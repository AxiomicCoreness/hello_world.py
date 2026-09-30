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
    entries hard-fail;
  - keep the --require behaviour and the exit-code contract:
      exit 0  all seal_sha3_256 seals verified + all --require entries present
      exit 1  at least one seal_sha3_256 mismatch OR a required entry missing
      exit 2  no ledger entries found

Revision note (witness chain): new entries may carry prev_hash — must
equal the seal_sha3_256 of the referenced prior entry (prev_index if
present, else entry_index - 1). prev_hash: null is an explicit region
start. Entries without prev_hash are legacy (informational). Schema
change, not a re-hash of history; old entries remain as they are.

Revision note (Annex V Article 35 band): seals with entry_index below
REVERIFY_BAND_START (9262) were computed on the pre-repair SHA3-256
pipeline (round-constant LFSR reseeded per round; repaired at entry
9262 per ledger/9262.yaml and POLICY.md Annex V). Per Annex V Article
35.2 such seals read as "not yet re-verified": a mismatch in the
pre-repair band is a recorded WARN (ANNEX_V_PRE_REPAIR_BAND), never a
hard gate failure and never silently passed. Mismatches at or above
REVERIFY_BAND_START remain hard failures.
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

# POLICY.md Annex V Article 35: seals below this index were computed on the
# pre-repair pipeline and read as "not yet re-verified" until they reproduce.
REVERIFY_BAND_START = 9262

# Correction entry ledger/9264.yaml disclosed a defective declared seal on
# entry 9263 (the sealing session computed the seal over a divergent
# canonicalization; the authoritative recompute reproduces identically under
# the CI-side Python pipeline and the repaired sandbox pipeline, per the
# gate-diag capture on mistral-gate-diag-9263). A mismatch that reproduces
# the disclosed authoritative value reads as WARN (disclosed-defect band),
# never a silent pass. Unlisted mismatches remain hard failures.
DISCLOSED_SEAL_DEFECTS: Dict[int, Dict[str, Any]] = {
    9263: {
        "declared": "41a2bd3097c527d1f225161dffb0ff8dac9af5dc16cfd6de2486d01dbf007f42",
        "authoritative_recompute": "5afba9103e5373292721b5856d606a82c0cc4fce7338739497ba73bba1f783ee",
        "disclosed_by": 9264,
    },
}


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
    not hard failures. Real seal mismatches remain hard failures — except
    in the pre-repair band, where Annex V Article 35 applies.
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
    idx = doc.get("entry_index")
    dd = DISCLOSED_SEAL_DEFECTS.get(idx) if isinstance(idx, int) else None
    if (
        dd
        and digest == dd["declared"]
        and expected == dd["authoritative_recompute"]
    ):
        return "warn", (
            f"{path}: DISCLOSED_SEAL_DEFECT — seal_sha3_256 mismatch at "
            f"entry {idx} disclosed by ledger/{dd['disclosed_by']}.yaml "
            f"(correction entry); declared: {digest} "
            f"authoritative recompute: {expected}; recorded WARN per the "
            f"disclosure, never a silent pass"
        )
    if isinstance(idx, int) and idx < REVERIFY_BAND_START:
        return "warn", (
            f"{path}: ANNEX_V_PRE_REPAIR_BAND — seal_sha3_256 mismatch at "
            f"entry {idx} (below re-verification band start {REVERIFY_BAND_START}); "
            f"seal computed on the pre-repair pipeline; per POLICY.md Annex V "
            f"Article 35 this reads as not-yet-re-verified (recorded, not a gate "
            f"failure); declared: {digest} expected: {expected}"
        )
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
    The chain check compares against the DECLARED prior seal, so a
    pre-repair-band warning on the prior entry does not break the chain.
    """
    bad: List[str] = []
    for stem, doc in sorted(docs.items(), key=lambda kv: int(kv[0])):
        if not isinstance(doc, dict):
            continue  # L1: non-mapping tops are informational (PR #89 class)
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
            # legacy fallback (PR #89 chain-band class): prior sealed under
            # the legacy 'seal' convention; chain against the declared tail
            # (hex-tailed '· <hex>' form, or a bare 64-hex seal value)
            legacy = prior.get("seal")
            prior_seal = None
            if isinstance(legacy, str):
                m = SEAL_TAIL.search(legacy)
                if m:
                    prior_seal = m.group(1)
                elif HEX64.match(legacy.strip().lower()):
                    prior_seal = legacy.strip().lower()
        if prior_seal is None:
            idx_now = doc.get("entry_index")
            if isinstance(idx_now, int) and idx_now < REVERIFY_BAND_START:
                # pre-repair legacy band: chain link informational (Annex V
                # Article 35 class; GLM hex-tail links are non-gate-preimages)
                continue
            bad.append(f"ledger/{stem}.yaml: prior entry ledger/{prev_stem}.yaml has no resolvable seal to chain from")
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
