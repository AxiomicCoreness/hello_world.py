# SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
# SPDX-License-Identifier: MIT
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

    # llama-server's GET /props: a ChatML template, so auto mode takes the chat route.
    props = {"chat_template": "{% for m in messages %}<|im_start|>{{ m.role }}\n{{ m.content }}<|im_end|>\n{% endfor %}"}
    gets: list = []

    def do_GET(self):  # noqa: N802
        type(self).gets.append(self.path)
        if self.path != "/props":
            self.send_response(404)
            self.end_headers()
            return
        out = json.dumps(type(self).props)
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(out.encode())

    def log_message(self, *a):  # silence
        pass


@pytest.fixture(autouse=True)
def _backend_env(monkeypatch):
    """Each test starts from the documented defaults: no fallback, empty liveness cache."""
    from src import llm_backend

    for k in ("LLM_BACKEND", "LLM_FALLBACK", "DEEPINFER_URL", "LLM_CLARKEYOURSATEE_URL", "LLM_ABLITERATED_URL", "DEEPINFER_REPROBE_S",
              "DEEPINFER_CONNECT_TIMEOUT", "LLM_RAW_REPLY", "LLM_SYSTEM_PROMPT", "LLM_HISTORY_MAX_TOKENS"):
        monkeypatch.delenv(k, raising=False)
    # Keep unit tests off the live history file and on the legacy reply guard by default
    # (raw/history behaviour is covered by dedicated tests below).
    monkeypatch.setenv("LLM_HISTORY_PATH", "")
    monkeypatch.setenv("LLM_RAW_REPLY", "0")
    llm_backend.reset_state()
    yield
    llm_backend.reset_state()


@pytest.fixture()
def stub_llm(monkeypatch):
    _Stub.requests = []
    _Stub.gets = []
    _Stub.status = 200
    srv = HTTPServer(("127.0.0.1", 0), _Stub)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    monkeypatch.setenv("LLM_URL", f"http://127.0.0.1:{srv.server_port}/v1/chat/completions")
    monkeypatch.setenv("LLM_MODEL", "stub-gguf")
    monkeypatch.setenv("LLM_BUILD_FEEDBACK", "0")
    monkeypatch.setenv("LLM_BACKEND", "gguf")  # these tests exercise the llama-server path directly
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
    monkeypatch.setenv("LLM_BACKEND", "gguf")
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
    monkeypatch.setenv("LLM_BACKEND", "gguf")  # LLM_URL is the gguf server's URL
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


USER_LOG_REPLY = "\n".join(f"User {i}: What are the lanes doing?" for i in range(1, 39))
DARK_ROOM_REPLY = (
    "The lanes are quiet right now. "
    + "They are just sitting in a dark room. " * 9
    + "The end."
)
NORMAL_REPLY = (
    "Lobula is busiest with 7 spikes in the last 2 s; antennal lobe 4, lateral horn 5, mushroom body 3.\n"
    "Fix: register capability 'zz' in toolkit.py before calling it."
)


def test_clean_reply_cuts_user_n_chat_log():
    out, notes = llm_chat.clean_reply(USER_LOG_REPLY)
    assert out == "" and len(notes) == 1 and "role echo" in notes[0]
    out, notes = llm_chat.clean_reply("Lanes 2 and 3 fire most.\nUser 1: hi\nUser 2: hi")
    assert out == "Lanes 2 and 3 fire most." and "role echo" in notes[0]
    out, _ = llm_chat.clean_reply("ok\n  Assistant 2: more\nSystem: x")
    assert out == "ok"


def test_clean_reply_cuts_repeat_loop_keeping_first_copy():
    out, notes = llm_chat.clean_reply(DARK_ROOM_REPLY)
    assert out == "The lanes are quiet right now. They are just sitting in a dark room."
    assert len(notes) == 1 and "repeat loop" in notes[0]
    # four occurrences is still allowed (limit is "more than 4")
    four = "a b c " * 2 + "x a b c a b c"
    assert llm_chat.clean_reply(four) == (four, [])


def test_clean_reply_leaves_normal_reply_unchanged():
    assert llm_chat.clean_reply(NORMAL_REPLY) == (NORMAL_REPLY, [])
    assert llm_chat.clean_reply("  " + NORMAL_REPLY + "\n") == (NORMAL_REPLY, [])


def test_request_carries_stops_and_repeat_penalties(stub_llm):
    llm_chat.handle_llm_sync(wire())
    body = stub_llm.requests[-1]["body"]
    for stop in ("<|im_end|>", "<|im_start|>", "User 1:", "\nUser:"):
        assert stop in body["stop"]
    assert body["repeat_penalty"] > 1.0 and body["frequency_penalty"] > 0
    assert stub_llm.gets == ["/props"], "auto mode probes the template once per call"
    assert stub_llm.requests[-1]["path"] == "/v1/chat/completions"
    # role messages only; llama-server applies the GGUF's own chat template
    assert [m["role"] for m in body["messages"]] == ["system", "user"]
    assert "<|im_start|>" not in json.dumps(body["messages"])


def test_guarded_reply_lines_through_bridge(stub_llm):
    original = stub_llm.reply
    stub_llm.reply = USER_LOG_REPLY
    try:
        lines = llm_chat.handle_llm_sync(wire())
    finally:
        stub_llm.reply = original
    assert not any(x.startswith("[Engine] llm: User") for x in lines)
    assert "[Engine] llm: (empty reply)" in lines
    assert "[System] llm route: backend=gguf path=/v1/chat/completions mode=auto family=chatml" in lines
    assert any(x.startswith("[System] llm: reply trimmed at a role echo") for x in lines)



def test_raw_reply_keeps_multiline_and_skips_guard(stub_llm, monkeypatch):
    monkeypatch.setenv("LLM_RAW_REPLY", "1")
    stub_llm.reply = "line one\n\nline two\nUser 1: echoed"
    lines = llm_chat.handle_llm_sync(wire("say anything"))
    engine = [x for x in lines if x.startswith("[Engine] llm:")]
    assert any("line one" in x for x in engine)
    assert any("line two" in x for x in engine)
    assert any("User 1: echoed" in x for x in engine)
    assert not any("reply trimmed" in x for x in lines)


def test_reply_prefix_uses_configured_model(monkeypatch):
    from src import llm_backend
    monkeypatch.setenv("LLM_CLARKEYOURSATEE_MODEL", "deepseek-r2-1.5b")
    assert llm_backend.reply_prefix("clarkeyoursatee") == "[ClarkeYoursaTee (deepseek-r2-1.5b)] "
    monkeypatch.setenv("LLM_CLARKEYOURSATEE_MODEL", llm_backend.DEFAULT_CLARKEYOURSATEE_MODEL)
    assert llm_backend.reply_prefix("clarkeyoursatee") == llm_backend.CLARKEYOURSATEE_PREFIX


def test_plain_prompt_without_neuro(stub_llm, monkeypatch):
    monkeypatch.setenv("LLM_RAW_REPLY", "1")
    lines = llm_chat.handle_llm_sync("/llm what is 2+2?")
    req = stub_llm.requests[-1]["body"]["messages"]
    assert req[0]["role"] == "system"
    assert "fruit-fly" not in req[0]["content"]
    assert req[-1]["content"] == "what is 2+2?"
    assert any("plain (no neuron snapshot" in x for x in lines)


def test_spike_prompt_forced_by_env(stub_llm, monkeypatch):
    monkeypatch.setenv("LLM_SYSTEM_PROMPT", "spike")
    lines = llm_chat.handle_llm_sync("/llm hi")
    req = stub_llm.requests[-1]["body"]["messages"]
    assert "fruit-fly" in req[0]["content"]
    assert "NEURON_SNAPSHOT:" in req[-1]["content"]


def test_history_persists_and_reloads(stub_llm, tmp_path, monkeypatch):
    hist = tmp_path / "llm_history.jsonl"
    monkeypatch.setenv("LLM_HISTORY_PATH", str(hist))
    monkeypatch.setenv("LLM_RAW_REPLY", "1")
    monkeypatch.setenv("LLM_HISTORY_MAX_TOKENS", "2500")
    stub_llm.reply = "Hello Clarke, I will remember."
    llm_chat.handle_llm_sync("/llm my name is Clarke, remember it")
    assert hist.is_file()
    rows = [json.loads(x) for x in hist.read_text().splitlines() if x.strip()]
    assert rows[0]["role"] == "user" and "Clarke" in rows[0]["content"]
    assert rows[1]["role"] == "assistant" and "remember" in rows[1]["content"].lower()
    # Simulate cold start: new process would re-read the same file
    stub_llm.requests.clear()
    stub_llm.reply = "Your name is Clarke."
    llm_chat.handle_llm_sync("/llm what is my name?")
    msgs = stub_llm.requests[-1]["body"]["messages"]
    roles = [m["role"] for m in msgs]
    assert roles[:1] == ["system"]
    assert "user" in roles[1:] and "assistant" in roles[1:]
    assert any(m["role"] == "user" and "Clarke" in m["content"] for m in msgs[:-1])
    assert msgs[-1]["content"] == "what is my name?"


def test_history_budget_keeps_newest(tmp_path, monkeypatch):
    hist = tmp_path / "llm_history.jsonl"
    monkeypatch.setenv("LLM_HISTORY_PATH", str(hist))
    # tiny budget: only the newest short turn fits
    turns = [
        {"role": "user", "content": "AAAA " * 200},
        {"role": "assistant", "content": "BBBB " * 200},
        {"role": "user", "content": "newest user"},
        {"role": "assistant", "content": "newest assistant"},
    ]
    hist.write_text("\n".join(json.dumps(t) for t in turns) + "\n", encoding="utf-8")
    kept = llm_chat.trim_history(llm_chat.load_history(hist), budget=20)
    assert kept
    assert kept[-1]["content"] == "newest assistant" or "newest" in kept[-1]["content"]
    assert all("AAAA" not in t["content"] for t in kept)


def test_llm_reset_archives_history(tmp_path, monkeypatch):
    hist = tmp_path / "llm_history.jsonl"
    hist.write_text(json.dumps({"role": "user", "content": "hi"}) + "\n", encoding="utf-8")
    monkeypatch.setenv("LLM_HISTORY_PATH", str(hist))
    lines = llm_chat.handle_llm_sync("/llm reset")
    assert any("history archived" in x for x in lines)
    assert not hist.exists()
    archives = list(tmp_path.glob("llm_history.jsonl.reset-*"))
    assert len(archives) == 1 and archives[0].read_text().startswith("{")
