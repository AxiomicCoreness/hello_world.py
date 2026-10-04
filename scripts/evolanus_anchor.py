#!/usr/bin/env python3
"""Evolanus anchor: the legendary tuple walked by the Eridanus flow.

The tuple is (token, position, scope). The walk is a step count.
The token is not a date, and the walk does not date it.
"""

from __future__ import annotations

import json

from scripts.eridanus_flow import run as eridanus_walk
from scripts.legend_anchor import LegendAnchor, ModelScope, Present

# Red marks on the GitHub history. They are cancelled Eridanus jobs
# and a pending commit status, not failed Python tests. Anchored here
# as the dual-host symbol shared with the GitCode pane.
RED_ANCHOR = (
    ("3a5d8b51", "legend-anchor", "github"),
    ("bb5138a3", "date-validation", "gitcode"),
    ("bbad8021", "slot-and-dual-layout", "github"),
    ("2eb44c76", "workflow-dependency", "gitcode"),
    ("a68b12b0", "eridanus-flow", "github"),
)


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
        "red_anchor": [
            {"commit": sha, "symbol": symbol, "pane": pane}
            for sha, symbol, pane in RED_ANCHOR
        ],
        "token_used_as_date": False,
    }


def main() -> int:
    print(json.dumps(walk(9268, steps=4), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
