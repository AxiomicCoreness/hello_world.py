"""Dual asyncio CI/CD loops (ledger 9174). No socket bind. MCP unfilled."""
from __future__ import annotations

from scripts.dual_asyncio_cicd import (
    BIND,
    DUAL_ASGI,
    FILLED,
    run_dual,
)


def test_dual_loops_green():
    report = run_dual()
    assert report["ok"] is True
    assert report["filled"] is False
    assert report["bind"] == "127.0.0.1"
    assert report["dual_asgi"] == "127.0.0.1:8024"
    assert report["control"]["lane"] == "control"
    assert report["deepseek"]["lane"] == "deepseek"
    assert report["deepseek"]["bind_0000"] is False


def test_constants():
    assert FILLED is False
    assert BIND != "0.0.0.0"
    assert "0.0.0.0" not in DUAL_ASGI
