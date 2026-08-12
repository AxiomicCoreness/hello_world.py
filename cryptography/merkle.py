#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Merkle tree (SHA-256) over ordered leaf digests.
Seal: ∀∞φ² · APP_MAIN_MERKLE_8653 · SEALED
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def leaf_hash(path: Path, content: bytes) -> str:
    # path-qualified leaf: H(path || 0x00 || content)
    return sha256_hex(path.as_posix().encode("utf-8") + b"\x00" + content)


def pair_hash(left: str, right: str) -> str:
    a, b = (left, right) if left <= right else (right, left)
    return sha256_hex(bytes.fromhex(a) + bytes.fromhex(b))


def merkle_root(leaves: Sequence[str]) -> str:
    if not leaves:
        return sha256_hex(b"")
    layer = list(leaves)
    while len(layer) > 1:
        nxt: List[str] = []
        for i in range(0, len(layer), 2):
            if i + 1 < len(layer):
                nxt.append(pair_hash(layer[i], layer[i + 1]))
            else:
                nxt.append(pair_hash(layer[i], layer[i]))  # duplicate odd leaf
        layer = nxt
    return layer[0]


def merkle_from_directory(
    root: Path,
    patterns: Optional[Sequence[str]] = None,
) -> Dict[str, Any]:
    """
    Build Merkle tree over files under root matching patterns (glob).
    Default: symplectic status artifacts + schema + generator.
    """
    root = root.resolve()
    if patterns is None:
        patterns = [
            "symplectic_status.py",
            "symplectic_status.json",
            "symplectic_status.agent.jsonl",
            "schemas/symplectic-status.json",
        ]

    files: List[Path] = []
    for pat in patterns:
        p = root / pat
        if p.is_file():
            files.append(p)
        else:
            files.extend(sorted(root.glob(pat)))

    # unique, sorted by relative path for stable ordering
    uniq = sorted({f.resolve() for f in files if f.is_file()}, key=lambda x: x.as_posix())

    leaves: List[Dict[str, str]] = []
    digests: List[str] = []
    for f in uniq:
        content = f.read_bytes()
        try:
            rel = f.relative_to(root)
        except ValueError:
            rel = Path(f.name)
        h = leaf_hash(rel, content)
        digests.append(h)
        leaves.append(
            {
                "path": rel.as_posix(),
                "sha256": sha256_hex(content),
                "leaf": h,
                "size": str(len(content)),
            }
        )

    return {
        "root_dir": str(root),
        "leaf_count": len(leaves),
        "merkle_root": merkle_root(digests),
        "algorithm": "sha256",
        "leaves": leaves,
    }


def inclusion_proof(leaves: Sequence[str], index: int) -> List[Tuple[str, str]]:
    """Return sibling path as list of (side, hash) where side is 'L' or 'R'."""
    if index < 0 or index >= len(leaves):
        raise IndexError("leaf index out of range")
    proof: List[Tuple[str, str]] = []
    layer = list(leaves)
    idx = index
    while len(layer) > 1:
        if len(layer) % 2 == 1:
            layer = layer + [layer[-1]]
        if idx % 2 == 0:
            sibling = layer[idx + 1]
            proof.append(("R", sibling))
        else:
            sibling = layer[idx - 1]
            proof.append(("L", sibling))
        nxt = []
        for i in range(0, len(layer), 2):
            nxt.append(pair_hash(layer[i], layer[i + 1]))
        layer = nxt
        idx //= 2
    return proof
