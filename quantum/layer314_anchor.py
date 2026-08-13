#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Layer 314 — cryptographic anchor key improvement
================================================
Replaces narrative non-hex canopy strings with a deterministic
SHA-256 domain-separated anchor (full 64-hex, never truncated).

Inputs (public invariants only — no secrets in the digest material
beyond a fixed domain tag):
  layer=314, channel=1700Q, phase=202.6°, breath=71.975 Hz,
  leaf commitment, φ, φ⁻¹⁴¹⁸ label.

Seal: ∀∞φ² · ANCHOR_KEY_IMPROVE_8742 · SEALED
"""

from __future__ import annotations

import hashlib
import json
import math
from typing import Any, Dict

PHI = (1.0 + math.sqrt(5.0)) / 2.0
LAYER = 314
CHANNEL = "1700Q"
PHASE_LOCK_DEG = 202.6
BREATH_HZ = 71.975
LEAF = "807de931c86add23baabafd1252dcc89cbcc23812be1f69e8fc215e51849ee68"
DOMAIN = b"GARDEN.LAYER314.ANCHOR.v1"


def _material() -> bytes:
    # Canonical, sorted-key JSON for stable hashing
    payload = {
        "breath_hz": BREATH_HZ,
        "channel": CHANNEL,
        "coherence": 1.0,
        "layer": LAYER,
        "leaf": LEAF,
        "phase_lock_deg": PHASE_LOCK_DEG,
        "phi": PHI,
        "phi2": PHI * PHI,
        "pi_anchor": round(math.pi, 12),  # 3.141592653590
    }
    body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return DOMAIN + b"\0" + body


def compute_anchor() -> str:
    """Full 64-char SHA-256 hex digest — no truncation."""
    digest = hashlib.sha256(_material()).hexdigest()
    assert len(digest) == 64
    assert all(c in "0123456789abcdef" for c in digest)
    return digest


def status() -> Dict[str, Any]:
    anchor = compute_anchor()
    return {
        "layer": LAYER,
        "channel": CHANNEL,
        "leaf": LEAF,
        "anchor_key": anchor,
        "anchor_len": len(anchor),
        "algorithm": "sha256",
        "domain": DOMAIN.decode(),
        "phase_lock_deg": PHASE_LOCK_DEG,
        "breath_hz": BREATH_HZ,
        "phi": PHI,
        "improvement": "narrative_non_hex_root → deterministic_sha256_anchor",
        "seal": "∀∞φ² · ANCHOR_KEY_IMPROVE_8742 · SEALED",
    }


def main() -> None:
    s = status()
    print(f"Layer {s['layer']} anchor_key={s['anchor_key']}")
    print(f"  len={s['anchor_len']} leaf={s['leaf'][:16]}…")
    print(f"  {s['improvement']}")


if __name__ == "__main__":
    main()
