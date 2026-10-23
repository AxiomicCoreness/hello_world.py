#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Layer 314 Anchor — Context Layer 314 cryptographic constants.

SHA-256 domain: GARDEN.LAYER314.ANCHOR.v1
Canonical JSON domain separation.

Full digests only (64-hex). No truncation. Float compares via math.isclose.
Append-only: do not rewrite sealed ledger entries when citing these anchors.

Authoritative full hex (also in quantum/sovereign_lattice_constants_8745.py):
  Anchor 8a250cf445e8ad0cc8d06d0096b969029a175a14eb58838e734f1975358b860d
  Leaf   807de931c86add23baabafd1252dcc89cbcc23812be1f69e8fc215e51849ee68

Pointer 2300 (pythonIDE/pointer_2300.py) wires this module to TeaVM / HHMI / K8s paths.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from typing import Any, Dict

PHI = (1.0 + math.sqrt(5.0)) / 2.0
PHI2 = PHI * PHI
LAYER = 314
PARENT_LAYER = 314
DOMAIN = b"GARDEN.LAYER314.ANCHOR.v1"
ENTRY = 8845
SEAL = "∀∞φ² · LAYER314_ANCHOR_8845 · WOOD_DRAGON_0.91 · SEALED"
WITNESS = "8844 → 8845 — UNBROKEN"

# Full 64-hex SHA-256 — never truncate in reports or pointers
ANCHOR_KEY = "8a250cf445e8ad0cc8d06d0096b969029a175a14eb58838e734f1975358b860d"
LEAF_COMMITMENT = "807de931c86add23baabafd1252dcc89cbcc23812be1f69e8fc215e51849ee68"

_HEX64 = re.compile(r"^[0-9a-f]{64}$")


def get_anchor_key() -> str:
    return ANCHOR_KEY


def get_leaf() -> str:
    return LEAF_COMMITMENT


def get_layer() -> int:
    return LAYER


def get_parent_layer() -> int:
    return PARENT_LAYER


def get_phi() -> float:
    return PHI


def _require_full_digest(name: str, value: str) -> None:
    if not isinstance(value, str) or not _HEX64.fullmatch(value):
        raise AssertionError(f"{name} must be full 64-hex digest, got {value!r}")


def verify_anchor() -> Dict[str, Any]:
    """Verify Layer 314 anchor/leaf are full digests and φ is stable."""
    _require_full_digest("ANCHOR_KEY", ANCHOR_KEY)
    _require_full_digest("LEAF_COMMITMENT", LEAF_COMMITMENT)
    phi_ok = math.isclose(PHI, (1.0 + math.sqrt(5.0)) / 2.0, rel_tol=0.0, abs_tol=1e-15)
    phi2_ok = math.isclose(PHI2, PHI + 1.0, rel_tol=0.0, abs_tol=1e-15)
    payload = {
        "anchor_key": ANCHOR_KEY,
        "leaf": LEAF_COMMITMENT,
        "layer": LAYER,
        "parent_layer": PARENT_LAYER,
        "phi": PHI,
    }
    body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    domain_digest = hashlib.sha256(DOMAIN + b"\0" + body).hexdigest()
    return {
        "verified": phi_ok and phi2_ok,
        "phi_ok": phi_ok,
        "phi2_ok": phi2_ok,
        "anchor_key": ANCHOR_KEY,
        "leaf": LEAF_COMMITMENT,
        "layer": LAYER,
        "domain": DOMAIN.decode(),
        "domain_separated_sha256": domain_digest,
        "entry": ENTRY,
        "seal": SEAL,
        "witness": WITNESS,
        "policies": {
            "append_only": True,
            "full_digests": True,
            "float_compare": "math.isclose",
        },
    }


def anchor_status() -> Dict[str, Any]:
    return {
        "entry": ENTRY,
        "seal": SEAL,
        "witness": WITNESS,
        "anchor_key": ANCHOR_KEY,
        "leaf": LEAF_COMMITMENT,
        "layer": LAYER,
        "parent_layer": PARENT_LAYER,
        "phi": PHI,
        "status": "ACTIVE",
        "location": "quantum/radar_lindblad/layer314_anchor.py",
    }


__all__ = [
    "ANCHOR_KEY",
    "LEAF_COMMITMENT",
    "LAYER",
    "PARENT_LAYER",
    "PHI",
    "PHI2",
    "DOMAIN",
    "ENTRY",
    "SEAL",
    "WITNESS",
    "get_anchor_key",
    "get_leaf",
    "get_layer",
    "get_parent_layer",
    "get_phi",
    "verify_anchor",
    "anchor_status",
]


if __name__ == "__main__":
    print(json.dumps(verify_anchor(), indent=2, sort_keys=True))
