"""Stub contract for 9174. Does not rewrite ledger/9174.yaml."""
from garden_surgery.dual_asyncio_cicd_9174_stub import (
    FILLED,
    DUAL_ASGI,
    dual_asyncio_cicd_9174,
)


def test_9174_stub_unfilled():
    body = dual_asyncio_cicd_9174()
    assert FILLED is False
    assert body["filled"] is False
    assert body["mcp_filled"] is False
    assert body["ledger_entry"] == 9174
    assert body["dual_asgi"] == "127.0.0.1:8024"
    assert "0.0.0.0" not in DUAL_ASGI
    assert body["harness_rewritten"] is False
