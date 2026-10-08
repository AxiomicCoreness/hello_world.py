#!/usr/bin/env python3
"""Relay a named slot to the intellect operator. Does not advance the ledger.

The intellect operator is not the inertia I. super_symplectic.py is not overwritten.
"""

from __future__ import annotations

import json

SLOT = "eridanus-dual-smoke"
OPERATOR = "intellect"
INERTIA = None


def relay() -> dict:
    return {
        "event": "/slot_relay_intellect",
        "slot": SLOT,
        "operator": OPERATOR,
        "I": INERTIA,
        "advances_head": False,
        "overwrites_super_symplectic": False,
    }


def main() -> int:
    print(json.dumps(relay(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
