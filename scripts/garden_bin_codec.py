#!/usr/bin/env python3
"""GARDEN.BIN.v1 codec — sealed manifests, not executables.

Stdlib only. Does not eval, exec, or bind sockets.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

MAGIC = "GARDEN.BIN.v1\n"
LAYER_ORDER = [
    "sovereign_core.bin",
    "ledger_tip.bin",
    "octonian_relay.bin",
    "adai_annihilator.bin",
]


def parse(path: Path) -> Tuple[str, Dict[str, Any]]:
    raw = path.read_text(encoding="utf-8")
    if not raw.startswith(MAGIC):
        raise ValueError(f"bad magic: {path.name}")
    payload = raw[len(MAGIC) :].strip()
    obj = json.loads(payload)
    if not isinstance(obj, dict):
        raise ValueError("payload must be object")
    return hashlib.sha3_256(raw.encode("utf-8")).hexdigest(), obj


def load_layers(root: Path) -> List[Tuple[str, str, Dict[str, Any]]]:
    out = []
    for name in LAYER_ORDER:
        digest, obj = parse(root / name)
        out.append((name, digest, obj))
    return out


def merkle(digests: List[str]) -> str:
    return hashlib.sha3_256("".join(digests).encode("utf-8")).hexdigest()
