#!/usr/bin/env python3
"""
scripts/parity_gitcode_atomgit.py
==================================
Mirror of scripts/traffic_cop.py for GitCode / AtomGit.

- Same 55-slot table (imported from traffic_cop.FILES — single source).
- Same formula: (day*1440 + hour*60 + minute) // 15 % 55.
- Returns the workflow name for the slot.
- Names a slot; does NOT dispatch.
- No socket, no HTTP, no gh/git CLI, no subprocess.
- Host adapters are declared as strings, not invoked.
"""

from __future__ import annotations

import datetime
import sys

from scripts.traffic_cop import FILES  # single source of truth

assert len(FILES) == 55, "table must be exactly 55 slots"
assert FILES[0] == "hypersurface.yml", "slot 0 is hypersurface.yml"

# Host adapters — declared, never invoked by this file.
# These are labels, not commands. The dispatch command for each host
# belongs to that host's own workflow file, not to this router.
HOSTS = {
    "github":   {"workflow_dir": ".github/workflows/"},
    "gitcode":  {"workflow_dir": ".gitcode/workflows/"},
    "atomgit":  {"workflow_dir": ".atomgit/workflows/"},
}


def slot_index(day: int, hour: int, minute: int) -> int:
    """Same integer formula as scripts/traffic_cop.py and workflow-parity.yml."""
    return (day * 1440 + hour * 60 + minute) // 15 % 55


def slot_name(idx: int) -> str:
    if not (0 <= idx <= 54):
        raise ValueError(f"slot out of range: {idx}")
    return FILES[idx]


def route(host: str, now: datetime.datetime | None = None) -> dict:
    if host not in HOSTS:
        raise ValueError(f"unknown host: {host}")
    now = now or datetime.datetime.now(datetime.timezone.utc)
    idx = slot_index(now.day, now.hour, now.minute)
    return {
        "host": host,
        "slot": idx,
        "name": slot_name(idx),
        "count": 1,
        "dispatch": False,
        "workflow_dir": HOSTS[host]["workflow_dir"],
    }


def main(argv: list[str]) -> int:
    host = argv[1] if len(argv) > 1 else "github"
    try:
        print(route(host))
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
