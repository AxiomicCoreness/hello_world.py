#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
anchor_mint_test.py — Verification of Entry 8745 Layer-326 Merkle root
======================================================================
MUST use domain-separated material matching mint time:
  GARDEN.LAYER326.MERKLE.v1 \0 + canonical JSON
  keys: anchor_key, layer, leaf, parent_layer, phi, timestamp

A bare JSON hash (no domain / leaf_commitment key) will NOT match.
"""

from __future__ import annotations

import hashlib
import json
import math
import sys

ANCHOR_KEY = "8a250cf445e8ad0cc8d06d0096b969029a175a14eb58838e734f1975358b860d"
LEAF = "807de931c86add23baabafd1252dcc89cbcc23812be1f69e8fc215e51849ee68"
LAYER = 326
PARENT_LAYER = 314
PHI = (1.0 + math.sqrt(5.0)) / 2.0
TIMESTAMP = "2026-08-13T22:11:28Z"
EXPECTED_ROOT = "08c344fe89bb5d476e34f693c6655efabf3731cab43919e8bdc18591377aca31"
DOMAIN = b"GARDEN.LAYER326.MERKLE.v1"


def compute_root() -> str:
    payload = {
        "anchor_key": ANCHOR_KEY,
        "layer": LAYER,
        "leaf": LEAF,
        "parent_layer": PARENT_LAYER,
        "phi": PHI,
        "timestamp": TIMESTAMP,
    }
    body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(DOMAIN + b"\0" + body).hexdigest()


def main() -> int:
    computed = compute_root()
    ok = computed == EXPECTED_ROOT and len(computed) == 64
    if ok:
        print("✅ TEST PASSED – Merkle root matches (domain-separated).")
        print(f"   Computed: {computed}")
        print(f"   Expected: {EXPECTED_ROOT}")
        print("✅ Anchor key and leaf commitment remain unchanged.")
        return 0
    print("❌ TEST FAILED – Root mismatch.")
    print(f"   Computed: {computed}")
    print(f"   Expected: {EXPECTED_ROOT}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
