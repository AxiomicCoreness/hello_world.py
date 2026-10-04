#!/usr/bin/env python3
"""Dual interaction layout for GitHub and GitCode.com.

Two panes, one position. Neither pane dispatches. The legend token
stays a name. Slot routing is a label, imported from the parity table.
"""

from __future__ import annotations

import datetime
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.legend_anchor import LegendAnchor, ModelScope, Present, governance_state
from scripts.parity_gitcode_atomgit import HOSTS, route

PANES = (
    {
        "host": "github",
        "site": "https://github.com",
        "repo": "AxiomicCoreness/hello_world.py",
    },
    {
        "host": "gitcode",
        "site": "https://gitcode.com",
        "repo": "AxiomicCoreness/hello_world.py",
    },
)


def layout(now: datetime.datetime | None = None) -> dict:
    now = now or datetime.datetime.now(datetime.timezone.utc)
    anchor = LegendAnchor(
        token="October 39, 2025",
        anchor_id="oct39-2025",
        governance_doc="POLICY.md",
    )
    scope = ModelScope(cutoff_utc="2026-08-01", witness="model training metadata")
    present = Present(anchor=anchor, head_index=0, head_seal="0" * 64, scope=scope)
    panes = []
    for pane in PANES:
        routed = route(pane["host"], now)
        panes.append({
            "site": pane["site"],
            "repo": pane["repo"],
            "workflow_dir": HOSTS[pane["host"]]["workflow_dir"],
            "slot": routed["slot"],
            "workflow": routed["name"],
            "dispatch": False,
            "interaction": "read",
        })
    return {
        "layout": "dual",
        "panes": panes,
        "present": governance_state(anchor, present)["present"],
        "note": "same position, two hosts; slot names a workflow and does not dispatch",
    }


def main() -> int:
    print(json.dumps(layout(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
