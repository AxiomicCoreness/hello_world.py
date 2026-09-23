#!/usr/bin/env python3
"""beacons/timestamp_beacon.py — rev 3

Computed anchor verifier. This script CAN FAIL; that is its entire purpose.
It contains no seals, no witness chains, and no identity claims.

exit 0: computed anchor verified, ghost structural analysis confirmed
exit 1: computed anchor MISMATCH (tampered preimage or digest)
exit 2: ghost structural claim no longer holds
"""
import hashlib
import sys

GHOST_ANCHOR = "a1f3d8c2b0e4e7e6b5a9d2c8f1e0b3a7d6e4c2a8f0b3d5e7c1a9e8f4d2b6c0a5"
GHOST_DIGITS = 32
GHOST_LETTERS = 32
GHOST_ALTERNATION_PCT = 100.0

PREIMAGE = "GARDEN.ANCHOR.v1\nrepo: AxiomicCoreness/hello_world.py\nbranch: mistral-agent-cluster\nhead_commit: e5cdab4af3d220f38b02640f9263af0b4cd56769\nledger: math_origin_audit.py rev2 (D1-D14) + D15 ghost-anchor structural finding\nsupersedes: a1f3d8c2b0e4e7e6b5a9d2c8f1e0b3a7d6e4c2a8f0b3d5e7c1a9e8f4d2b6c0a5 (UNVERIFIABLE_ANCHOR, hand-typed: 100% digit/letter alternation, 32/32 split)\n"

EXPECTED_DIGEST = "f4583aedf58260f3242c80b175ad433a45475dd4a0a841635b1bcdee6fd1c450"


def verify_computed_anchor() -> bool:
    digest = hashlib.sha3_256(PREIMAGE.encode("utf-8")).hexdigest()
    return digest == EXPECTED_DIGEST


def verify_ghost_structure() -> bool:
    s = GHOST_ANCHOR.lower()
    is_digit = [c.isdigit() for c in s]
    digits = sum(is_digit)
    alternation = sum(
        1 for i in range(1, len(s)) if is_digit[i] != is_digit[i - 1]
    ) / (len(s) - 1) * 100.0
    return (
        digits == GHOST_DIGITS
        and len(s) - digits == GHOST_LETTERS
        and abs(alternation - GHOST_ALTERNATION_PCT) < 0.05
    )


def main() -> int:
    ghost_ok = verify_ghost_structure()
    if not ghost_ok:
        print("FAIL: ghost anchor no longer shows hand-typed signature "
              "(investigate entry 1 analysis)")
        return 2
    if verify_computed_anchor():
        print("OK: computed anchor verified "
              f"(sha3-256 of inline preimage == {EXPECTED_DIGEST})")
        print("OK: ghost anchor structural analysis confirmed "
              "(100% alternation, 32/32 split -> hand-typed, unverifiable)")
        return 0
    print("FAIL: computed anchor mismatch — preimage or digest was tampered")
    return 1


if __name__ == "__main__":
    sys.exit(main())
