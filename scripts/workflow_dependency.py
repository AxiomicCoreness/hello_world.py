#!/usr/bin/env python3
"""Workflow dependency graph. Names edges. Does not dispatch.

legend_anchor is a position label. It is not an input to a differential
equation. The DE family is a downstream module that may cite the position
and must not convert the legend token.
"""

from __future__ import annotations

import json

EDGES = (
    {"from": "tilelang/cadence_quadratic.py", "to": "scripts/test_slot_boundary.py", "kind": "test"},
    {"from": "scripts/traffic_cop.py", "to": "scripts/parity_gitcode_atomgit.py", "kind": "table"},
    {"from": "scripts/parity_gitcode_atomgit.py", "to": "scripts/dual_interaction_layout.py", "kind": "label"},
    {"from": "scripts/legend_anchor.py", "to": "scripts/dual_interaction_layout.py", "kind": "position"},
    {"from": "scripts/legend_anchor.py", "to": "scripts/eridanus_flow.py", "kind": "label-only"},
    {"from": ".github/workflows/workflow-parity.yml", "to": ".github/workflows/eridanus-dual-smoke.yml", "kind": "slot-name"},
    {"from": ".github/workflows/eridanus-dual-smoke.yml", "to": "ledger/", "kind": "forbidden"},
)


def graph() -> dict:
    return {
        "legend_anchor": "position, not a time, not a DE input",
        "de_home": "scripts/eridanus_flow.py — not yet written; not appended to legend_anchor.py",
        "dual_layout": "read-only panes; dispatch forbidden",
        "edges": list(EDGES),
    }


def main() -> int:
    print(json.dumps(graph(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
