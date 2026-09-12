#!/usr/bin/env python3
"""
pythonIDE/verify_hmac_chain.py

Read-only verification of the append-only HMAC chain produced by
pythonIDE/attenuation_learning.py.

- Re-derives every chain head from prev + mac.
- Re-derives every mac from the canonical body.
- Confirms genesis head = sha3_256(REPO_URL).
- Confirms attribution hex is separate from the chain head.
- Confirms precedent 8206 is referenced, never rewritten.

Exit code 0 on clean chain, 1 on any mismatch.

Ledger policy: NO_LEDGER_WRITE
Precedent: garden_surgery/attenuation_package_confirmed.py (entry 8206)
Next free ledger index: 9237+
"""

from __future__ import annotations
import argparse
import hashlib
import hmac
import json
import sys
from pathlib import Path
from typing import Dict, Any, List

REPO_URL = "https://github.com/AxiomicCoreness/hello_world.py/"
HMAC_KEY = b"garden.attenuation.hmac.v1"
ATTRIBUTION = "DeepSeek 2.2.2(4)"
ATTRIBUTION_HEX = hashlib.sha3_256(ATTRIBUTION.encode("utf-8")).hexdigest()
PRECEDENT_ENTRY = 8206
PRECEDENT_HEX = (
    "e46de633154a35b13d75e1863f97a32102571fa370bb02ca08166e0868356699"
)
PRECEDENT_WITNESS = "8205 → 8206 — UNBROKEN"

DEFAULT_CHAIN = "ledger/attenuation_chain.jsonl"


def _canonical_body(prev: str, event: str, payload: Dict[str, Any],
                    ts: str, repo: str, attribution: str) -> str:
    """Reproduce the exact canonicalization used at append time."""
    body = {
        "prev": prev,
        "event": event,
        "payload": payload,
        "ts": ts,
        "repo": repo,
        "attribution": attribution,
    }
    return json.dumps(body, sort_keys=True, separators=(",", ":"))


def _recompute_mac(prev: str, event: str, payload: Dict[str, Any],
                   ts: str) -> str:
    canon = _canonical_body(prev, event, payload, ts, REPO_URL, ATTRIBUTION)
    return hmac.new(
        HMAC_KEY, canon.encode("utf-8"), hashlib.sha3_256
    ).hexdigest()


def _recompute_head(prev: str, mac: str) -> str:
    return hashlib.sha3_256((prev + mac).encode("utf-8")).hexdigest()


def verify(chain_path: Path, verbose: bool = False) -> int:
    genesis_expected = hashlib.sha3_256(REPO_URL.encode("utf-8")).hexdigest()

    if not chain_path.is_file():
        print(f"❌ chain file not found: {chain_path}", file=sys.stderr)
        return 1

    records: List[Dict[str, Any]] = []
    with chain_path.open("r", encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"❌ line {lineno}: invalid JSON: {e}", file=sys.stderr)
                return 1

    if not records:
        print("❌ chain is empty", file=sys.stderr)
        return 1

    # ── 1. genesis head ─────────────────────────────────────────
    first = records[0]
    if first.get("prev") != genesis_expected:
        print(f"❌ genesis mismatch: prev={first.get('prev')} "
              f"expected={genesis_expected}", file=sys.stderr)
        return 1
    if first.get("head") != genesis_expected:
        # The first record's head equals the genesis head by construction.
        print(f"❌ first head != genesis: {first.get('head')}",
              file=sys.stderr)
        return 1

    # ── 2. walk the chain ───────────────────────────────────────
    for i, rec in enumerate(records):
        # 3. attribution separation
        if rec.get("attribution") != ATTRIBUTION:
            print(f"❌ record {i}: attribution label mismatch", file=sys.stderr)
            return 1
        if rec.get("attribution_hex") != ATTRIBUTION_HEX:
            print(f"❌ record {i}: attribution_hex mismatch", file=sys.stderr)
            return 1
        if rec.get("attribution_hex") == rec.get("head"):
            print(f"❌ record {i}: attribution_hex collides with head",
                  file=sys.stderr)
            return 1

        # 4. precedent reference
        if rec.get("precedent") != PRECEDENT_ENTRY:
            print(f"❌ record {i}: precedent entry mismatch", file=sys.stderr)
            return 1
        if rec.get("precedent_hex") != PRECEDENT_HEX:
            print(f"❌ record {i}: precedent hex mismatch", file=sys.stderr)
            return 1
        if rec.get("witness") != PRECEDENT_WITNESS:
            print(f"❌ record {i}: witness string mismatch", file=sys.stderr)
            return 1

        # 2. MAC re-derivation
        mac_expected = _recompute_mac(
            prev=rec["prev"],
            event=rec["event"],
            payload=rec["payload"],
            ts=rec.get("ts", ""),
        )
        if not hmac.compare_digest(mac_expected, rec["mac"]):
            print(f"❌ record {i}: MAC mismatch", file=sys.stderr)
            return 1

        # 2. head re-derivation
        head_expected = _recompute_head(rec["prev"], rec["mac"])
        if not hmac.compare_digest(head_expected, rec["head"]):
            print(f"❌ record {i}: head mismatch", file=sys.stderr)
            return 1

        # link: next.prev == this.head
        if i + 1 < len(records):
            nxt = records[i + 1]
            if nxt["prev"] != rec["head"]:
                print(f"❌ record {i}→{i+1}: broken link", file=sys.stderr)
                return 1

        if verbose:
            print(f"  ✓ record {i:3d} head={rec['head'][:16]}... "
                  f"event={rec['event']}")

    # ── 3. summary ──────────────────────────────────────────────
    head = records[-1]["head"]
    print("=" * 72)
    print("HMAC CHAIN VERIFICATION")
    print("=" * 72)
    print(f"records          = {len(records)}")
    print(f"genesis          = {genesis_expected}")
    print(f"final head       = {head}")
    print(f"attribution      = {ATTRIBUTION}")
    print(f"attribution hex  = {ATTRIBUTION_HEX}")
    print(f"precedent        = {PRECEDENT_ENTRY}")
    print(f"precedent hex    = {PRECEDENT_HEX}")
    print(f"witness          = {PRECEDENT_WITNESS}")
    print(f"ledger policy    = NO_LEDGER_WRITE")
    print("=" * 72)
    print("✅ chain verified — every link re-derived, no rewrites")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Verify the append-only HMAC chain emitted by "
                    "attenuation_learning.py."
    )
    ap.add_argument("--chain", default=DEFAULT_CHAIN,
                    help=f"path to chain JSONL (default: {DEFAULT_CHAIN})")
    ap.add_argument("-v", "--verbose", action="store_true",
                    help="print each verified link")
    args = ap.parse_args()
    return verify(Path(args.chain), verbose=args.verbose)


if __name__ == "__main__":
    sys.exit(main())
