#!/usr/bin/env python3
"""
port_380_gate.py — Scaling Gate bound to Port 380

Deterministic by default. Resonant Spike (φ⁵⁵ scale) only under explicit auth_override.
Does NOT auto-fire on Path C; use --override for manual trigger.
"""

from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path

PHI = (1 + math.sqrt(5)) / 2
SPIKE_INTENSITY = PHI**55  # ≈ 3.121e11
BASE_ORDER = 1.778e11  # original specification magnitude
DEFAULT_HARMONY = 0.7337473231  # Strike X reference index
TEMPORAL_ANCHOR = 2026.058
ROOT = Path("/home/workdir/artifacts")


def apply_strike_x_gate(
    harmony_index: float,
    temporal_anchor: float = TEMPORAL_ANCHOR,
    auth_override: bool = False,
) -> dict:
    """
    Pure function.
    auth_override=False → return index unchanged (deterministic default).
    auth_override=True  → multiply by SPIKE_INTENSITY / BASE_ORDER (Resonant Spike).
    """
    if not auth_override:
        return {
            "harmony_index": harmony_index,
            "mode": "deterministic_default",
            "scaling_factor": 1.0,
            "auth_override": False,
            "temporal_anchor": temporal_anchor,
        }

    scaling_factor = SPIKE_INTENSITY / BASE_ORDER
    scaled = harmony_index * scaling_factor
    return {
        "harmony_index": scaled,
        "mode": "resonant_spike",
        "scaling_factor": scaling_factor,
        "auth_override": True,
        "temporal_anchor": temporal_anchor,
        "spike_intensity": SPIKE_INTENSITY,
        "base_order": BASE_ORDER,
    }


def main():
    p = argparse.ArgumentParser(description="Port 380 Scaling Gate")
    p.add_argument("--harmony", type=float, default=DEFAULT_HARMONY)
    p.add_argument("--override", action="store_true", help="Enable Resonant Spike (explicit)")
    p.add_argument("--anchor", type=float, default=TEMPORAL_ANCHOR)
    args = p.parse_args()

    out = apply_strike_x_gate(args.harmony, args.anchor, auth_override=args.override)
    print("=" * 72)
    print("PORT 380 SCALING GATE")
    print("=" * 72)
    print(f"input harmony   = {args.harmony}")
    print(f"mode            = {out['mode']}")
    print(f"scaling_factor  = {out['scaling_factor']}")
    print(f"output harmony  = {out['harmony_index']}")
    print(f"auth_override   = {out['auth_override']}")
    print("seal: ∀∞φ² · PORT_380_SCALING_GATE_8707 · SEALED")
    Path("/tmp/port_380_gate_result.json").write_text(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
