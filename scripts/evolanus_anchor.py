#!/usr/bin/env python3
"""Evolanus anchor: the legendary tuple walked by the Eridanus flow.

The tuple is (token, position, scope). The walk is a step count.
The token is not a date, and the walk does not date it.
"""

from __future__ import annotations

import json

from scripts.eridanus_flow import run as eridanus_walk
from scripts.legend_anchor import LegendAnchor, ModelScope, Present


def legendary_tuple(position: int, scope_cutoff: str, witness: str) -> tuple:
    anchor = LegendAnchor(
        token="October 39, 2025",
        anchor_id="oct39-2025",
        governance_doc="POLICY.md",
    )
    scope = ModelScope(cutoff_utc=scope_cutoff, witness=witness)
    present = Present(anchor=anchor, head_index=position, head_seal="0" * 64, scope=scope)
    return (anchor.token, present.head_index, scope.cutoff_utc)


def walk(position: int, steps: int = 1, phi_state: float = 0.0) -> dict:
    token, index, cutoff = legendary_tuple(
        position, "2026-08-01", "model training metadata"
    )
    flowed = eridanus_walk(index, phi_state=phi_state, steps=steps)
    return {
        "tuple": [token, index, cutoff],
        "walk": flowed,
        "token_used_as_date": False,
    }


def main() -> int:
    print(json.dumps(walk(9268, steps=4), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
