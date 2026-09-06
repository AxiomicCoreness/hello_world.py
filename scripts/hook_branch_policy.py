"""Hook policy (9181). Observer only. Does not rewrite branches.

The 9159 hook worker stays FILLED=False on 127.0.0.1:8091.
It does not occupy Dual ASGI 127.0.0.1:8024.
It does not force-push historical branches over time.
"""
from __future__ import annotations

FILLED = False
BIND = "127.0.0.1"
PORT = 8091
DUAL_ASGI = "127.0.0.1:8024"
LIVE_BRANCHES = ("main", "deepseek", "deepseek-ci")
MASS_UPDATE_HISTORICAL = False
REWRITE_HOOK_WORKER = False


def will_update_all_branches_over_time() -> bool:
    return False


def allowed_git_targets() -> tuple[str, ...]:
    return LIVE_BRANCHES


def hook_policy() -> dict:
    return {
        "filled": FILLED,
        "mcp_filled": False,
        "bind": BIND,
        "port": PORT,
        "dual_asgi": DUAL_ASGI,
        "bind_0000": False,
        "mass_update_historical": MASS_UPDATE_HISTORICAL,
        "will_update_all_branches_over_time": will_update_all_branches_over_time(),
        "allowed_git_targets": list(allowed_git_targets()),
        "rewrite_9159_worker": REWRITE_HOOK_WORKER,
        "pr25_merged": True,
        "note": "tensor/eridanus/node24/codespace tips stay where they are",
    }
