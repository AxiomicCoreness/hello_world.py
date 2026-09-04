"""Load and verify GARDEN.BIN.v1 layer files."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

MAGIC = b"GARDEN.BIN.v1\n"
LAYER_ORDER = [
    "sovereign_core.bin",
    "ledger_tip.bin",
    "octonian_relay.bin",
    "adai_annihilator.bin",
]


def _decode_payload(data: bytes, name: str) -> Dict[str, Any]:
    if data.startswith(MAGIC):
        payload = data[len(MAGIC) :]
    else:
        payload = data
    try:
        obj = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        raise ValueError(f"Invalid JSON in {name}: {e}") from e
    if not isinstance(obj, dict):
        raise ValueError(f"payload must be object: {name}")
    return obj


def parse(path: Path) -> Tuple[str, Dict[str, Any]]:
    data = path.read_bytes()
    digest = hashlib.sha3_256(data).hexdigest()
    return digest, _decode_payload(data, path.name)


def load_layers(root: Path) -> List[Tuple[str, str, Dict[str, Any]]]:
    """Return list of (name, sha3-256 digest, decoded json) for each layer."""
    result = []
    for name in LAYER_ORDER:
        path = root / name
        if not path.exists():
            raise FileNotFoundError(f"Missing layer: {path}")
        digest, obj = parse(path)
        result.append((name, digest, obj))
    return result


def merkle(digests: List[str]) -> str:
    """SHA3-256 of concatenated layer digests in LAYER_ORDER."""
    return hashlib.sha3_256("".join(digests).encode("utf-8")).hexdigest()
