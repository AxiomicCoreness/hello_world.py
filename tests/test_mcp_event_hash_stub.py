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
    assert block["hex"] == "226e6589c7233ba762b5817bbd601c962325dbf3ae94c1b79fcb967adc25c839"  # GARDEN.EVENT.v1.LEDGER domain; sealed 9189 terminal_hex is historical (append-only)
    assert preview_payload(9189, "/actualized_dual_asyncio_cicd_appended_math_origin").startswith("9189|")
