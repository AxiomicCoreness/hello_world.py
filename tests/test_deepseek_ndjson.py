"""Pure tests for DeepSeek NDJSON stream — no API key required."""
from __future__ import annotations

import json

from quantum.deepseek_mesh.dsh_adapter import (
    MODE_OFFLINE,
    complete_stream,
    offline_stream,
    probe,
)


def test_probe_reports_ndjson():
    p = probe()
    assert p.get("stream") == "NDJSON"
    assert MODE_OFFLINE in p.get("modes", [])


def test_offline_stream_events():
    events = list(offline_stream("hello garden", chunk_size=16))
    kinds = [e["event"] for e in events]
    assert kinds[0] == "start"
    assert kinds[-1] == "complete"
    assert "delta" in kinds
    assert events[-1]["mode"] == MODE_OFFLINE
    assert events[-1]["text"]
    assert "seal" in events[-1]


def test_complete_stream_offline_prefer():
    events = list(complete_stream("ci", prefer="offline"))
    assert events[0]["event"] == "start"
    assert events[-1]["event"] == "complete"
    body = "".join(e.get("text", "") for e in events if e["event"] == "delta")
    assert "GARDEN_OFFLINE_ECHO" in body or "echo" in body.lower() or body


def test_ndjson_lines_serializable():
    for ev in offline_stream("x"):
        line = json.dumps(ev)
        assert json.loads(line)["event"] in ("start", "delta", "complete")
