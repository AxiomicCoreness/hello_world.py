from garden_surgery.singularity_spec_9185_stub import (
    FILLED,
    singularity_spec_9185,
)


def test_spec_is_not_runtime():
    body = singularity_spec_9185()
    assert FILLED is False
    assert body["executable_paste"] is False
    assert body["mcp_filled"] is False
    assert body["ledger_entry"] == 9185
    assert body["rewrite_9184"] is False
