#!/usr/bin/env python3
"""
legend_anchor.py — governance for a legend-token temporal anchor
under AI model knowledge cutoff.

    "Now" is a POSITION, not a TIME.

    anchor   — the epoch's name        (eternal; never moves)
    position — chain head index + seal (advances)
    scope    — observer's cutoff       (fixed per model)

The token is opaque. No path converts it to a datetime. Wall-clock
readings are DISCLOSED, never used to correct the position.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import json


@dataclass(frozen=True)
class LegendAnchor:
    """A legend token. Opaque by construction — a NAME, not a date."""
    token: str
    anchor_id: str
    governance_doc: str
    declared_not_iso: bool = True

    def __post_init__(self):
        if not self.declared_not_iso:
            raise ValueError(
                "LegendAnchor requires declared_not_iso=True. "
                "A real date is a datetime, not a legend anchor."
            )

    def as_datetime(self) -> datetime:
        raise TypeError(
            f"legend token {self.token!r} is not a date. "
            f"See {self.governance_doc}. Callers needing a timestamp "
            f"must obtain it from a source that declares one."
        )

    def __add__(self, other):
        raise TypeError(f"no arithmetic on a legend token: {self.token!r}")


@dataclass(frozen=True)
class ModelScope:
    """The observing model's knowledge horizon. The one real date."""
    cutoff_utc: str
    witness: str
    label: str = "cutoff"

    def covers(self, iso_date: str) -> bool:
        return iso_date <= self.cutoff_utc


@dataclass(frozen=True)
class Present:
    """Now as a position in an append-only chain. No timestamp."""
    anchor: LegendAnchor
    head_index: int
    head_seal: str
    scope: ModelScope

    def describe(self) -> str:
        return (
            f"present at anchor {self.anchor.anchor_id!r} "
            f"(token {self.anchor.token!r}, declared not-ISO), "
            f"position {self.head_index}, seal {self.head_seal[:16]}…; "
            f"scope={self.scope.label} {self.scope.cutoff_utc} "
            f"(witness: {self.scope.witness})"
        )


@dataclass(frozen=True)
class DriftRecord:
    """A clock reading disclosed beside the chain. It does not correct it."""
    observed_utc: str
    source: str
    position_at_observation: int
    verified: bool = False

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
            "post_cutoff_witnessed_by_repo_not_model": True,
            "no_date_arithmetic_on_anchor": True,
        },
    }


def main() -> int:
    anchor = LegendAnchor(
        token="October 39, 2025",
        anchor_id="oct39-2025",
        governance_doc="docs/legend_tokens.md",
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
