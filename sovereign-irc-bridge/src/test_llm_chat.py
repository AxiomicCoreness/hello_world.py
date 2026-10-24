"""/llm bridge path against a stubbed llama-server (no model download)."""
from __future__ import annotations

import json
import socket
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

from src import llm_chat
from src.cli_loopback import create_app

NEURO = {
    "v": 1, "mode": "lif", "brain": "lif", "song_ms": 5230, "brain_ms": 5200, "window_ms": 2000,
    "lanes": [{"lane": i, "label": f"L{i}", "spikes": i, "rate_hz": i / 2, "last_ms": 5100,
               "v_mv": -52.0, "total": 10 + i} for i in range(4)],
    "total_spikes": 46, "top": [{"id": "lane3", "region": "L3", "spikes": 13, "ms_since": 100}],
}
FEEDBACK = {"kind": "traceback", "dropped": 0, "reports": [
    {"type": "CapabilityError", "message": "unknown capability 'zz'", "origin": "cli",
     "frames": ["toolkit.py:88 in call", "cli_loopback.py:470 in handle_pythonide"]}]}


def wire(prompt="what is the brain doing?", neuro=NEURO, fb=FEEDBACK):
    s = f"/llm {prompt}"
    if neuro is not None:
        s += "\n#neuro " + json.dumps(neuro)
    if fb is not None:
        s += "\n#feedback " + json.dumps(fb)
    return s


class _Stub(BaseHTTPRequestHandler):
    requests: list = []
    reply = "Lane L3 is busiest. Fix: register capability 'zz' in toolkit.py."
    status = 200

    def do_POST(self):  # noqa: N802
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        type(self).requests.append({"path": self.path, "body": body})
        out = json.dumps({"choices": [{"message": {"role": "assistant", "content": type(self).reply}}]})
        self.send_response(type(self).status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(out.encode())

    def log_message(self, *a):  # silence
        pass


@pytest.fixture()
def stub_llm(monkeypatch):
    _Stub.requests = []
    _Stub.status = 200
    srv = HTTPServer(("127.0.0.1", 0), _Stub)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    monkeypatch.setenv("LLM_URL", f"http://127.0.0.1:{srv.server_port}/v1/chat/completions")
    monkeypatch.setenv("LLM_MODEL", "stub-gguf")
    monkeypatch.setenv("LLM_BUILD_FEEDBACK", "0")
    yield _Stub
    srv.shutdown()
    srv.server_close()


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def test_llm_line_detection():
    assert llm_chat.is_llm_line("/llm hi")
    assert llm_chat.is_llm_line("/LLM hi\n#neuro {}")
    assert llm_chat.is_llm_line("/llm")
    assert not llm_chat.is_llm_line("/llmx")
    assert not llm_chat.is_llm_line("/py call golden_ratio")


def test_parse_wire_and_bad_json():
    p, n, f, notes = llm_chat.parse_wire(wire())
    assert p == "what is the brain doing?" and n == NEURO and f == FEEDBACK and notes == []
    p, n, f, notes = llm_chat.parse_wire("/llm hi\n#neuro {nope\n#feedback []")
    assert n is None and f is None and len(notes) == 2


def test_llm_path_hits_stub_with_snapshot_and_feedback(stub_llm):
    lines = llm_chat.handle_llm_sync(wire())
    assert "[Engine] llm: Lane L3 is busiest. Fix: register capability 'zz' in toolkit.py." in lines
    assert any("spikes[L0=0 L1=1 L2=2 L3=3]" in x for x in lines)
    req = stub_llm.requests[-1]
    assert req["path"] == "/v1/chat/completions"
    assert req["body"]["model"] == "stub-gguf"
    msgs = req["body"]["messages"]
    assert msgs[0]["role"] == "system" and "FEEDBACK" in msgs[0]["content"]
    assert "dopamine" not in json.dumps(msgs).lower() and "reward" not in json.dumps(msgs).lower()
    user = msgs[1]["content"]
    assert '"total_spikes":46' in user
    assert "CapabilityError" in user and "toolkit.py:88 in call" in user
    assert user.endswith("USER: what is the brain doing?")


def test_llm_offline_is_a_line_not_a_crash(monkeypatch):
    monkeypatch.setenv("LLM_URL", f"http://127.0.0.1:{_free_port()}/v1/chat/completions")
    monkeypatch.setenv("LLM_BUILD_FEEDBACK", "0")
    monkeypatch.setenv("LLM_TIMEOUT_S", "2")
    lines = llm_chat.handle_llm_sync(wire())
    assert lines[-1].startswith("[System] llm offline:")


def test_llm_http_error_is_offline_line(stub_llm):
    stub_llm.status = 503
    lines = llm_chat.handle_llm_sync(wire())
    assert lines[-1].startswith("[System] llm offline: HTTP 503")


def test_non_loopback_llm_url_refused(monkeypatch):
    for bad in ("http://0.0.0.0:8081/v1/chat/completions", "http://10.0.0.5:8081/x",
                "http://api.example.com/v1/chat/completions", "file:///etc/passwd"):
        with pytest.raises(llm_chat.LlmConfigError):
            llm_chat.assert_loopback_url(bad)
        monkeypatch.setenv("LLM_URL", bad)
        lines = llm_chat.handle_llm_sync("/llm hi")
        assert lines[-1].startswith("[System] llm offline: LLM_URL must be")


def test_feedback_merge_truncates_and_caps():
    big = {"kind": "traceback", "dropped": 4, "reports": [
        {"type": "E" * 500, "message": "m" * 5000, "frames": [f"f{i}.py:{i}" for i in range(10)]}
        for _ in range(9)]}
    out = llm_chat.merge_feedback(big, [])
    assert len(json.dumps(out, ensure_ascii=False)) <= llm_chat.MAX_FEEDBACK_JSON
    assert out["reports"], "at least one report survives"
    r = out["reports"][-1]
    assert len(r["type"]) == 80 and len(r["message"]) == llm_chat.MAX_MESSAGE
    assert r["frames"] == ["f7.py:7", "f8.py:8", "f9.py:9"]
    assert out["dropped"] == 4 + 9 - len(out["reports"])


def test_surefire_failures_become_feedback(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("LLM_BUILD_FEEDBACK", raising=False)
    (tmp_path / "zz.ZzFailTest.txt").write_text(
        "-------------------------------------------------------------------------------\n"
        "Test set: zz.ZzFailTest\n"
        "-------------------------------------------------------------------------------\n"
        "Tests run: 1, Failures: 1, Errors: 0, Skipped: 0, Time elapsed: 0.034 s <<< FAILURE! -- in zz.ZzFailTest\n"
        "zz.ZzFailTest.boom -- Time elapsed: 0.018 s <<< FAILURE!\n"
        "org.opentest4j.AssertionFailedError: lane count ==> expected: <1> but was: <2>\n"
        "\tat org.junit.jupiter.api.AssertionFailureBuilder.build(AssertionFailureBuilder.java:151)\n"
        "\tat zz.ZzFailTest.boom(ZzFailTest.java:2)\n"
    )
    (tmp_path / "ok.OkTest.txt").write_text("Tests run: 3, Failures: 0, Errors: 0, Skipped: 0\n")
    reports = llm_chat.collect_build_feedback(tmp_path)
    assert reports == [{
        "type": "org.opentest4j.AssertionFailedError",
        "message": "lane count ==> expected: <1> but was: <2>",
        "origin": "mvn-test",
        "frames": ["zz.ZzFailTest.boom", "zz.ZzFailTest.boom(ZzFailTest.java:2)"],
    }]


def test_websocket_llm_round_trip(stub_llm):
    from fastapi.testclient import TestClient

    client = TestClient(create_app())
    with client.websocket_connect("/cli") as ws:
        banner = [ws.receive_text() for _ in range(5)]
        assert any("/llm" in b for b in banner)
        ws.send_text(wire())
        got = []
        while not any(x.startswith("[Engine] llm:") for x in got):
            got.append(ws.receive_text())
    assert got[-1].startswith("[Engine] llm: Lane L3")
    assert stub_llm.requests, "bridge forwarded to the stub model server"


def test_run_refuses_wildcard_bind(monkeypatch):
    from src import cli_loopback

    monkeypatch.setenv("CLI_BIND_HOST", "0.0.0.0")
    with pytest.raises(SystemExit) as e:
        cli_loopback.run()
    assert e.value.code == 1
    monkeypatch.setenv("CLI_BIND_HOST", "127.0.0.1")
    monkeypatch.setenv("LLM_URL", "http://192.168.1.9:8081/v1/chat/completions")
    with pytest.raises(SystemExit):
        cli_loopback.run()


def test_cli_port_is_6680_and_not_browser_restricted():
    # Chrome kRestrictedPorts / Firefox gBadPortList include IRC 6665-6669, 6679 (Firefox), 6697.
    from src import cli_loopback

    assert cli_loopback.CLI_PORT == 6680
    assert cli_loopback.CLI_PORT not in {6665, 6666, 6667, 6668, 6669, 6679, 6697}
    assert cli_loopback.LOOPBACK_HOST == "127.0.0.1"


def test_neuro_line_shows_window_end_and_song_total():
    n = dict(NEURO, window_end_ms=22400, window_anchor="last_spike")
    line = llm_chat._neuro_line(n)
    assert "spikes[L0=0 L1=1 L2=2 L3=3]" in line
    assert line.endswith(" end=22400ms(last_spike) total=46")
    assert llm_chat._neuro_line(NEURO).endswith("spikes[L0=0 L1=1 L2=2 L3=3] total=46")
