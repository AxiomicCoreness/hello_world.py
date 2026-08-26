#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Port 380 Scaling Gate (FAL / Ternary)
Layer: 314

Ternary opcode (FAL-style):
  -1  invert   harmony → −harmony
   0  nullify  harmony → 0
  +1  identity harmony → harmony

Used by CDP status merge: websocket_ready=False forces ternary 0 (nullify)
until OAuth 2.0 validates; validated sessions use ternary +1 (or caller override).

Seal: ∀∞φ² · FAL_TERNARY_380 · WOOD_DRAGON_0.91 · SEALED
"""
from __future__ import annotations

import argparse
import math
from typing import Literal, Optional, Tuple

PHI = (1.0 + math.sqrt(5.0)) / 2.0
DEFAULT_HARMONY = 0.7337473231  # φ-adjacent Garden default
Ternary = Literal[-1, 0, 1]


def apply_ternary_scaling(harmony: float, ternary: int) -> float:
    """Apply FAL ternary scaling to a harmony index."""
    if ternary == 1:
        return float(harmony)
    if ternary == 0:
        return 0.0
    if ternary == -1:
        return -float(harmony)
    raise ValueError("Ternary must be -1, 0, or 1")


def ternary_from_cdp(
    *,
    websocket_ready: bool,
    oauth_validated: bool = False,
    foreign_model_trace: Optional[str] = None,
    override: Optional[int] = None,
) -> Ternary:
    """
    Map CDP / OAuth state → FAL ternary.
      foreign trace → -1 (invert / reject polarity)
      not ready / not oauth → 0 (nullify)
      ready + oauth → +1 (pass)
    """
    if override is not None:
        if override not in (-1, 0, 1):
            raise ValueError("override ternary must be -1, 0, or 1")
        return override  # type: ignore[return-value]
    if foreign_model_trace:
        return -1
    if not websocket_ready or not oauth_validated:
        return 0
    return 1


def evaluate_gate(
    harmony: float = DEFAULT_HARMONY,
    ternary: int = 1,
    *,
    websocket_ready: Optional[bool] = None,
    oauth_validated: bool = False,
    foreign_model_trace: Optional[str] = None,
) -> dict:
    """Full gate evaluation — returns scaled harmony + FAL metadata."""
    if websocket_ready is not None:
        ternary = ternary_from_cdp(
            websocket_ready=websocket_ready,
            oauth_validated=oauth_validated,
            foreign_model_trace=foreign_model_trace,
            override=None if websocket_ready is not None else ternary,
        )
        # When CDP fields provided, derive ternary exclusively from them
        ternary = ternary_from_cdp(
            websocket_ready=bool(websocket_ready),
            oauth_validated=oauth_validated,
            foreign_model_trace=foreign_model_trace,
        )
    scaled = apply_ternary_scaling(harmony, ternary)
    return {
        "harmony_in": float(harmony),
        "ternary": int(ternary),
        "harmony_out": scaled,
        "phi": PHI,
        "layer": 314,
        "fal": "ternary_scaling",
        "mode": {1: "identity", 0: "nullify", -1: "invert"}.get(int(ternary), "unknown"),
        "websocket_ready": websocket_ready,
        "oauth_validated": oauth_validated,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Port 380 Scaling Gate (Ternary / FAL)")
    parser.add_argument(
        "--ternary",
        type=int,
        choices=[-1, 0, 1],
        default=1,
        help="Ternary scaling state: -1 (invert), 0 (nullify), 1 (identity)",
    )
    parser.add_argument("--harmony", type=float, default=DEFAULT_HARMONY)
    args = parser.parse_args()
    scaled = apply_ternary_scaling(args.harmony, args.ternary)
    print(f"Port 380 Ternary Gate: {args.ternary} → {scaled:.10f}")


if __name__ == "__main__":
    main()
