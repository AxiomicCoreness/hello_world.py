#!/usr/bin/env python3
"""
witness_chain_check.py — Grok node wiring for the three contracts.

Read-only. No ledger write. No network.

  emit          print all three contracts
  list          print contract names
  assert-count  exit 0 iff exactly three contracts
"""

from __future__ import annotations

import sys
from pathlib import Path

# Support both package import and path-local load on CI
try:
    from pythonIDE.witness_chain_triple import CONTRACTS, emit
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from pythonIDE.witness_chain_triple import CONTRACTS, emit  # type: ignore


def cmd_list() -> int:
    for name, _ in CONTRACTS:
        print(name)
    return 0


def cmd_assert_count() -> int:
    n = len(CONTRACTS)
    print(json_count(n))
    return 0 if n == 3 else 2


def json_count(n: int) -> str:
    import json

    return json.dumps({"contract_count": n, "ok": n == 3, "node": "grok-skill_tensor"})


def main(argv: list[str]) -> int:
    if not argv or argv[0] in ("-h", "--help", "help"):
        print(__doc__)
        return 0
    cmd = argv[0]
    if cmd == "emit":
        emit()
        return 0
    if cmd == "list":
        return cmd_list()
    if cmd == "assert-count":
        return cmd_assert_count()
    print(f"unknown command: {cmd}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
