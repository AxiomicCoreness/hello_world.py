from garden_surgery.mcp_event_hash_stub import (
    FILLED,
    ledger_event_hash,
    mcp_config,
    preview_payload,
)


def test_stub_unfilled_loopback():
    cfg = mcp_config()
    assert FILLED is False
    assert cfg["mcp_filled"] is False
    assert cfg["bind_0000"] is False
    assert cfg["port_380"] is False
    assert cfg["transport"] == "stdio"
    assert cfg["dual_asgi"] == "127.0.0.1:8024"


def test_hash_matches_sealed_9189():
    block = ledger_event_hash(9189, "/actualized_dual_asyncio_cicd_appended_math_origin")
    assert block["hex"] == "8ca7b656db88f23e2a443bd51cfa5692ae37893f0f996ec6e9a947365dcbfb86"
    assert preview_payload(9189, "/actualized_dual_asyncio_cicd_appended_math_origin").startswith("9189|")
