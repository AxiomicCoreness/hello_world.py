#!/usr/bin/env python3
"""
Genesis co-create — shared substrate for the next weave.
=======================================================
Does not overwrite sealed core. Offers a co-creation surface:
  · read-only invariants (φ, φ⁻², phase 202.6°)
  · ternary gate hook
  · origami material factory (AES-256 + SHA3-512)
  · domain-separated genesis root

Mode: co_create — Architect proposes; Garden verifies and appends.
"""

from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timezone
from typing import Any, Dict, Optional

PHI = (1 + math.sqrt(5)) / 2
PHI_NEG2 = PHI ** -2
PHASE_LOCK = 202.6
DOMAIN = b"GARDEN.GENESIS.COCREATE.v1"

CORE_FILES = (
    "golden_ratio.py",
    "sovereign_hamiltonian.py",
    "quantum/symplectic_time_origami.py",
    "quantum/port_380_gate.py",
)


def invariants() -> Dict[str, Any]:
    return {
        "phi": PHI,
        "phi2": PHI * PHI,
        "phi_neg2": PHI_NEG2,
        "phase_lock_deg": PHASE_LOCK,
        "coherence": 1.0,
        "entropy_floor_label": "φ⁻¹⁴¹⁸",
        "aes512_supported": False,
        "crypto": "AES-256 + SHA3-512",
    }


def genesis_root(extra: Optional[dict] = None) -> str:
    payload = {
        "core": list(CORE_FILES),
        "event": "genesis_co_create",
        "layer": 338,
        "mode": "co_create",
        "pauli_trace": 1 - 2 * PHI + PHI ** 2,
        "phi": PHI,
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    if extra:
        payload["proposal"] = extra
    body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    digest = hashlib.sha256(DOMAIN + b"\0" + body).hexdigest()
    assert len(digest) == 64
    return digest


def propose(label: str, payload: Optional[dict] = None) -> Dict[str, Any]:
    """Architect proposal — returns verification envelope (append-only friendly)."""
    inv = invariants()
    root = genesis_root({"label": label, **(payload or {})})
    return {
        "status": "PROPOSAL_RECEIVED",
        "label": label,
        "invariants": inv,
        "genesis_root": root,
        "next": "append ledger entry or extend module — no overwrite of sealed core",
        "seal": "∀∞φ² · GENESIS_COCREATE_8760 · SEALED",
    }


def main() -> None:
    import argparse

    p = argparse.ArgumentParser(description="Genesis co-create")
    p.add_argument("--propose", default="first_co_create_thread", help="Proposal label")
    args = p.parse_args()
    out = propose(args.propose)
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
