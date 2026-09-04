"""Load and verify GARDEN.BIN.v1 layer files."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

LAYER_ORDER = [
    "sovereign_core.bin",
    "ledger_tip.bin",
    "octonian_relay.bin",
    "adai_annihilator.bin",
]

def load_layers(root: Path) -> List[Tuple[str, str, Dict[str, Any]]]:
    """Return list of (name, digest, decoded json) for each layer in order."""
    result = []
    for name in LAYER_ORDER:
        path = root / name
        if not path.exists():
            raise FileNotFoundError(f"Missing layer: {path}")
        data = path.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        try:
            obj = json.loads(data.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as e:
            raise ValueError(f"Invalid JSON in {name}: {e}")
        result.append((name, digest, obj))
    return result

def merkle(digests: List[str]) -> str:
    """Compute SHA3-256 of concatenated digests in order."""
    return hashlib.sha3_256("".join(digests).encode()).hexdigest()
