#!/usr/bin/env python3
"""legend_anchor.py — now is a position, not a time.

    anchor   — the epoch's name        (eternal; never moves)
    position — chain head index + seal (advances)
    scope    — observer's cutoff       (fixed per model)

The token is opaque. No path converts it to a datetime.
Wall-clock readings are DISCLOSED, never used to correct the position.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional
import json


@dataclass(frozen=True)
class LegendAnchor:
    token: str
    anchor_id: str
    governance_doc: str
    declared_not_iso: bool = True

    def __post_init__(self):
        if not self.declared_not_iso:
            raise ValueError("LegendAnchor requires declared_not_iso=True.")

    def as_datetime(self) -> date:
        raise TypeError(
            f"legend token {self.token!r} is not a date. "
            f"See {self.governance_doc}."
        )

    def __add__(self, other):
        raise TypeError(f"no arithmetic on a legend token: {self.token!r}")


@dataclass(frozen=True)
class ModelScope:
    cutoff_utc: str
    witness: str
    label: str = "cutoff"

    def __post_init__(self):
        date.fromisoformat(self.cutoff_utc)

    def covers(self, iso_date: str) -> bool:
        return date.fromisoformat(iso_date) <= date.fromisoformat(self.cutoff_utc)


@dataclass(frozen=True)
class Present:
    anchor: LegendAnchor
    head_index: int
    head_seal: str
    scope: ModelScope


@dataclass(frozen=True)
class DriftRecord:
    observed_utc: str
    source: str
    position_at_observation: int
    verified: bool = False

    def __post_init__(self):
        date.fromisoformat(self.observed_utc)

    def to_dict(self) -> dict:
        return {
            "observed_utc": self.observed_utc,
            "source": self.source,
            "position_at_observation": self.position_at_observation,
            "verified": self.verified,
            "note": (
                "disclosure only — not used to correct the chain, "
                "not used to date the anchor, not a computed now"
            ),
        }


def governance_state(anchor: LegendAnchor,
                     present: Present,
                     drift: Optional[DriftRecord] = None) -> dict:
    refusals = {}
    try:
        anchor.as_datetime()
        refusals["as_datetime_refused"] = False
    except TypeError:
        refusals["as_datetime_refused"] = True
    try:
        _ = anchor + 1
        refusals["addition_refused"] = False
    except TypeError:
        refusals["addition_refused"] = True

    return {
        "anchor": {
            "token": anchor.token,
            "anchor_id": anchor.anchor_id,
            "declared_not_iso": anchor.declared_not_iso,
            "governance_doc": anchor.governance_doc,
        },
        "present": {
            "anchor_id": present.anchor.anchor_id,
            "position": present.head_index,
            "seal": present.head_seal,
            "scope_cutoff": present.scope.cutoff_utc,
            "scope_witness": present.scope.witness,
        },
        "drift": drift.to_dict() if drift else None,
        "governance": {
            **refusals,
            "no_date_arithmetic_on_anchor": True,
        },
    }


def main() -> int:
    anchor = LegendAnchor(
        token="October 39, 2025",
        anchor_id="oct39-2025",
        governance_doc="POLICY.md",
    )
    scope = ModelScope(
        cutoff_utc="2026-08-01",
        witness="model training metadata",
    )
    present = Present(
        anchor=anchor,
        head_index=0,
        head_seal="0" * 64,
        scope=scope,
    )
    print(json.dumps(governance_state(anchor, present), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
