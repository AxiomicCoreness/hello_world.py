"""ARGO-facing sink — Section IV stub. No runtime binding. MCP FILLED=False."""
from __future__ import annotations
from typing import Any, Dict

BIND = "127.0.0.1:8024"
FILLED = False
LEDGER_GENESIS = 9195


def handle_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "ok": False,
        "reason": "STUB — Section IV sink not activated",
        "ledger_genesis": LEDGER_GENESIS,
        "bind": BIND,
        "mcp_filled": FILLED,
    }


if __name__ == "__main__":
    print("Section IV sink stub — no binding. MCP FILLED=False.")
