#!/usr/bin/env python3
"""
.container/aklt_gap.py — AKLT-point gap, sourced.

Emergent correction to docs/aklt_research_notes.md §7.

§7 correctly cites the isotropic Heisenberg gap (Δ ≈ 0.41049(2),
White–Huse DMRG 1993). That value belongs to H = Σ S_i·S_{i+1}, not to
the AKLT point. The AKLT point sits elsewhere in the bilinear-biquadratic
phase diagram:

    H(θ) = Σ [ cos(θ) S_i·S_{i+1} + sin(θ) (S_i·S_{i+1})² ]
    AKLT point:  tan(θ_AKLT) = 1/3   →   θ_AKLT ≈ 0.32175 rad

The AKLT-point gap is nonzero, distinct from the Heisenberg gap, and has
no simple closed form. Any numeric value asserted here must carry its
source; the module refuses to fabricate one (K2, K6).

Callers set AKLT_GAP with SourcedGap(value, source). Until set, the gate
reports PENDING rather than VERIFIED.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class SourcedGap:
    value: float
    source: str
    uncertainty: Optional[float] = None

    @property
    def is_sourced(self) -> bool:
        return bool(self.source and self.source.strip())


AKLT_GAP: Optional[SourcedGap] = None

HEISENBERG_GAP: SourcedGap = SourcedGap(
    value=0.41049,
    uncertainty=0.00002,
    source="White & Huse, Phys. Rev. B 48, 3844 (1993), DMRG on N=22",
)

import math
THETA_AKLT_RAD: float = math.atan(1.0 / 3.0)


def gate_aklt_gap() -> tuple[str, str]:
    """Return (verdict, message)."""
    if AKLT_GAP is None or not AKLT_GAP.is_sourced:
        return (
            "PENDING",
            "AKLT-point gap not sourced — supply "
            "AKLT_GAP = SourcedGap(value, source) to close notes §7",
        )
    if AKLT_GAP.value <= 0.0:
        return ("FALSE", f"AKLT gap must be > 0, got {AKLT_GAP.value}")
    unc = AKLT_GAP.uncertainty if AKLT_GAP.uncertainty is not None else "—"
    return (
        "VERIFIED",
        f"AKLT gap = {AKLT_GAP.value} ± {unc}  [{AKLT_GAP.source}]",
    )


if __name__ == "__main__":
    v, m = gate_aklt_gap()
    print(f"[{v}] {m}")
    print()
    print("Adjacent value for reference (not the AKLT point):")
    print(f"  Heisenberg Δ = {HEISENBERG_GAP.value} ± "
          f"{HEISENBERG_GAP.uncertainty}  [{HEISENBERG_GAP.source}]")
    print(f"  AKLT θ ≈ {THETA_AKLT_RAD:.5f} rad "
          f"(tan θ = 1/3, bilinear-biquadratic param.)")
