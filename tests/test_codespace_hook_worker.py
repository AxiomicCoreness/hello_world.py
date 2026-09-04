"""Import and contract checks for scripts/codespace_hook_worker.py (ledger 9159).

Does not bind a socket. Does not start uvicorn. MCP remains FILLED=False.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path


def _load():
    root = Path(__file__).resolve().parents[1]
    path = root / "scripts" / "codespace_hook_worker.py"
    spec = importlib.util.spec_from_file_location("codespace_hook_worker", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def test_hook_worker_contract():
    mod = _load()
    assert mod.FILLED is False
    assert mod.BIND == "127.0.0.1"
    assert mod.PORT == 8091
    assert mod.DUAL_ASGI == "127.0.0.1:8024"
    assert "/hook/ledger" in mod.ALLOWLIST
    assert hasattr(mod, "app")


def test_hook_worker_no_wildcard_bind():
    mod = _load()
    assert mod.BIND != "0.0.0.0"
    assert "0.0.0.0" not in mod.DUAL_ASGI
