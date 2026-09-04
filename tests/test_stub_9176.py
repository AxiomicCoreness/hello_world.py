from garden_surgery.today_commit_trace_9176_stub import today_commit_trace_9176


def test_9176_stub_points_at_sealed_yaml():
    body = today_commit_trace_9176()
    assert body["ledger_entry"] == 9176
    assert body["module"] == "ledger/9176.yaml"
    assert body["mcp_filled"] is False
    assert body["dual_asgi"] == "127.0.0.1:8024"
    assert body["ledger_to_commit"][9175] == "5e7f32c1"
    assert body["backfill_commit"].startswith("2a079312")
    assert body["witness_prefix"].startswith("9bbb38f8")
