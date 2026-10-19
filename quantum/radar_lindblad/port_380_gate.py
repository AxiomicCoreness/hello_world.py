#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Port 380 Scaling Gate (FAL / Pentad rank)
Layer: 314

Pentad rank opcode (FAL-style), balanced five-level set {−2, −1, 0, +1, +2}:
  -2  strong_invert    harmony → −2·harmony
  -1  invert           harmony → −harmony
   0  nullify          harmony → 0
  +1  identity         harmony → harmony
  +2  strong_identity  harmony → 2·harmony

The ternary subset {−1, 0, +1} behaves exactly as before. ±2 is reachable
only by explicit override (CLI, HTTP body, function argument).

Used by CDP status merge: websocket_ready=False forces ternary 0 (nullify)
until OAuth 2.0 validates; validated sessions use ternary +1 (or caller override).
CDP/OAuth derivation only ever yields −1, 0 or +1.

Seal: ∀∞φ² · FAL_TERNARY_380 · WOOD_DRAGON_0.91 · SEALED
"""
from __future__ import annotations

import argparse
import math
from typing import Literal, Optional, Tuple

PHI = (1.0 + math.sqrt(5.0)) / 2.0
DEFAULT_HARMONY = 0.7337473231  # φ-adjacent Garden default
Pentad = Literal[-2, -1, 0, 1, 2]
Ternary = Literal[-1, 0, 1]  # compat: the subset CDP/OAuth derivation yields

PENTAD_VALUES: Tuple[int, ...] = (-2, -1, 0, 1, 2)
TERNARY_VALUES: Tuple[int, ...] = (-1, 0, 1)
PENTAD_MODES = {
    -2: "strong_invert",
    -1: "invert",
    0: "nullify",
    1: "identity",
    2: "strong_identity",
}


def _is_rank(value: object, allowed: Tuple[int, ...]) -> bool:
    try:
        return value in allowed
    except TypeError:
        return False


def apply_ternary_scaling(harmony: float, ternary: int) -> float:
    """Apply FAL ternary scaling to a harmony index (strict {-1, 0, 1})."""
    if not _is_rank(ternary, TERNARY_VALUES):
        raise ValueError("Ternary must be -1, 0, or 1")
    return apply_pentad_scaling(harmony, ternary)


def apply_pentad_scaling(harmony: float, rank: int) -> float:
    """Apply FAL pentad scaling: ±1 as before, ±2 is twice the ±1 result."""
    if rank == 1:
        return float(harmony)
    if rank == 0:
        return 0.0
    if rank == -1:
        return -float(harmony)
    if rank == 2:
        return 2.0 * float(harmony)
    if rank == -2:
        return -2.0 * float(harmony)
    raise ValueError("Pentad rank must be -2, -1, 0, 1, or 2")


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
        if not _is_rank(override, PENTAD_VALUES):
            raise ValueError("override rank must be -2, -1, 0, 1, or 2")
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
    scaled = apply_pentad_scaling(harmony, ternary)
    return {
        "harmony_in": float(harmony),
        "ternary": int(ternary),
        "harmony_out": scaled,
        "phi": PHI,
        "layer": 314,
        "fal": "ternary_scaling",
        "mode": PENTAD_MODES.get(int(ternary), "unknown"),
        "websocket_ready": websocket_ready,
        "oauth_validated": oauth_validated,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Port 380 Scaling Gate (Pentad / FAL)")
    parser.add_argument(
        "--ternary",
        "--pentad",
        dest="ternary",
        type=int,
        choices=list(PENTAD_VALUES),
        default=1,
        help=(
            "Pentad rank: -2 (strong invert), -1 (invert), 0 (nullify), "
            "1 (identity), 2 (strong identity)"
        ),
    )
    parser.add_argument("--harmony", type=float, default=DEFAULT_HARMONY)
    args = parser.parse_args()
    scaled = apply_pentad_scaling(args.harmony, args.ternary)
    print(f"Port 380 Ternary Gate: {args.ternary} → {scaled:.10f}")


if __name__ == "__main__":
    main()
