#!/usr/bin/env python3
"""M92 wisdom transmission — 144 packets (21+34+55+34), SHA3-256 Merkle."""
from __future__ import annotations

import hashlib
import json
import math
from typing import Any, Dict, List, Tuple

PHI = (1.0 + math.sqrt(5.0)) / 2.0
LAYERS: List[Tuple[str, int]] = [
    ("Foundation", 21),
    ("Harmonic", 34),
    ("Sovereign", 55),
    ("Cosmic", 34),
]
DECLARED_ROOT = (
    "7F3A8E2C4B6D0F1A9C8E2F4A6B8D0C2E4F6A8B0D2F4C6E8A0C2E4F6B8D0A2C4E6"
)


def leaf_digest(layer: str, n: int) -> bytes:
    raw = f"M92|{layer}|{n}|phi={PHI:.15f}|w={PHI ** (-n):.16e}".encode("utf-8")
    return hashlib.sha3_256(raw).digest()


def build_leaves() -> List[bytes]:
    leaves: List[bytes] = []
    n = 0
    for name, count in LAYERS:
        for _ in range(count):
            n += 1
            leaves.append(leaf_digest(name, n))
    return leaves


def merkle_levels(leaves: List[bytes]) -> List[List[bytes]]:
    level = list(leaves)
    levels = [level]
    while len(level) > 1:
        nxt: List[bytes] = []
        i = 0
        while i < len(level):
            a = level[i]
            b = level[i + 1] if i + 1 < len(level) else a
            nxt.append(hashlib.sha3_256(a + b).digest())
            i += 2
        level = nxt
        levels.append(level)
    return levels


def report() -> Dict[str, Any]:
    leaves = build_leaves()
    levels = merkle_levels(leaves)
    root = levels[-1][0].hex()
    return {
        "packets": 144,
        "layers": {name: count for name, count in LAYERS},
        "leaf_nodes": len(leaves),
        "tree_depth": len(levels) - 1,
        "total_nodes": sum(len(lv) for lv in levels),
        "internal_nodes": sum(len(lv) for lv in levels[1:]),
        "computed_root_sha3_256": root,
        "declared_root": DECLARED_ROOT,
        "declared_root_verified": root.lower() == DECLARED_ROOT.lower(),
        "phi": PHI,
        "phi13": PHI ** 13,
        "rate_packets_per_sec": PHI * 1e6,
        "status": "TRANSMISSION_RECORDED",
    }


if __name__ == "__main__":
    print(json.dumps(report(), indent=2))
