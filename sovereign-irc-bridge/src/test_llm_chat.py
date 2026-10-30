# SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
# SPDX-License-Identifier: MIT
"""/llm bridge path against a stubbed llama-server (no model download)."""
from __future__ import annotations

import json
import os
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
        banner = [ws.receive_text() for _ in range(6)]
        assert any("/llm" in b for b in banner)
        assert any("llm session: default" in b for b in banner)
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
    assert any("session=default history archived" in x for x in lines)
    assert not hist.exists()
    archives = list(tmp_path.glob("llm_history.jsonl.reset-default-*"))
    assert len(archives) == 1 and archives[0].read_text().startswith("{")


# ---------------------------------------------------------------------------
# DeepSeek tutor + DeepInfer atomic history rewrite (PR #155)
#
# The DeepSeek tutor suggested a ``chat/history_manager.py`` HistoryManager, a
# ``chat/capability.py`` module and an HTTP ``/llm`` route in
# ``api/module_routes.py``. None of those paths exist in this repo: ``/llm`` is
# a command on the ``/cli`` WebSocket (cli_loopback.py, 127.0.0.1:6680). Each
# suggestion is mapped onto the real code in ``src/llm_chat.py`` and
# ``src/cli_loopback.py``; every test below names the suggestion it covers.
# ---------------------------------------------------------------------------


class TestDeepSeekTutorAtomicHistory:
    """DeepSeek tutor history suggestions, as implemented in llm_chat.py / cli_loopback.py."""

    def test_session_id_validation(self):
        """Tutor: per-session HistoryManager keyed by a session id.

        Real: ``llm_chat.normalize_session`` — ``[A-Za-z0-9_-]{1,64}``, anything else → ``default``.
        """
        assert llm_chat.normalize_session(None) == "default"
        assert llm_chat.normalize_session("") == "default"
        assert llm_chat.normalize_session("abc_12-Z") == "abc_12-Z"
        assert llm_chat.normalize_session("bad/id") == "default"
        assert llm_chat.normalize_session("x" * 65) == "default"
        assert llm_chat.normalize_session("ok" * 32) == "ok" * 32  # exactly 64

    def test_per_session_history_isolation(self, tmp_path, monkeypatch):
        """Tutor: per-session history (HistoryManager.get/append per session).

        Real: ``append_history(..., session=)`` / ``load_history(session=)`` over one JSONL
        whose rows carry a ``session`` field.
        """
        hist = tmp_path / "llm_history.jsonl"
        monkeypatch.setenv("LLM_HISTORY_PATH", str(hist))
        llm_chat.append_history("alpha-user", "alpha-asst", session="alpha")
        llm_chat.append_history("beta-user", "beta-asst", session="beta")
        a = llm_chat.load_history(session="alpha")
        b = llm_chat.load_history(session="beta")
        d = llm_chat.load_history(session="default")
        assert [t["content"] for t in a] == ["alpha-user", "alpha-asst"]
        assert [t["content"] for t in b] == ["beta-user", "beta-asst"]
        assert d == []
        rows = [json.loads(x) for x in hist.read_text().splitlines() if x.strip()]
        assert all("session" in r for r in rows)

    def test_legacy_rows_map_to_default(self, tmp_path, monkeypatch):
        """Tutor: migrate old history without breaking it.

        Real: ``_row_session`` — rows written before sessions (no ``session`` field) load as ``default``.
        """
        hist = tmp_path / "llm_history.jsonl"
        hist.write_text(
            json.dumps({"role": "user", "content": "legacy hi"}) + "\n"
            + json.dumps({"role": "assistant", "content": "legacy bye"}) + "\n"
            + json.dumps({"role": "user", "content": "other", "session": "s2"}) + "\n",
            encoding="utf-8",
        )
        monkeypatch.setenv("LLM_HISTORY_PATH", str(hist))
        assert [t["content"] for t in llm_chat.load_history(session="default")] == ["legacy hi", "legacy bye"]
        assert [t["content"] for t in llm_chat.load_history(session="s2")] == ["other"]
        assert llm_chat.load_history(session="missing") == []

    def test_session_scoped_llm_reset(self, tmp_path, monkeypatch):
        """Tutor: ``clear(session)`` only drops that session.

        Real: ``/llm reset`` → ``archive_history(session=)`` moves only that session's rows to
        ``*.reset-<session>-<utc>`` (rewrite, never delete); other sessions stay live.
        """
        hist = tmp_path / "llm_history.jsonl"
        monkeypatch.setenv("LLM_HISTORY_PATH", str(hist))
        llm_chat.append_history("keep-u", "keep-a", session="keep")
        llm_chat.append_history("drop-u", "drop-a", session="drop")
        lines = llm_chat.handle_llm_sync("/llm reset", session="drop")
        assert any("session=drop history archived" in x for x in lines)
        assert hist.exists()
        kept = [json.loads(x) for x in hist.read_text().splitlines() if x.strip()]
        assert all(r.get("session") == "keep" for r in kept)
        assert [t["content"] for t in llm_chat.load_history(session="keep")] == ["keep-u", "keep-a"]
        assert llm_chat.load_history(session="drop") == []
        archives = list(tmp_path.glob("llm_history.jsonl.reset-drop-*"))
        assert len(archives) == 1
        archived = [json.loads(x) for x in archives[0].read_text().splitlines() if x.strip()]
        assert all(r.get("session") == "drop" for r in archived)

    def test_atomic_rewrite_survives_simulated_crash(self, tmp_path, monkeypatch):
        """Tutor: atomic save (write ``.tmp`` then rename).

        Real: ``_atomic_rewrite`` — ``.tmp`` + fsync + ``os.replace``; a stale ``.tmp`` left by a
        crash is never read as live history.
        """
        hist = tmp_path / "llm_history.jsonl"
        monkeypatch.setenv("LLM_HISTORY_PATH", str(hist))
        llm_chat.append_history("u1", "a1", session="s1")
        llm_chat.append_history("u2", "a2", session="s2")
        original = hist.read_text()
        tmp = hist.with_name(hist.name + ".tmp")
        tmp.write_text('{"role":"user","content":"CORRUPT","session":"s1"}\n', encoding="utf-8")
        assert hist.read_text() == original
        dest = llm_chat.archive_history(session="s1")
        assert dest is not None and dest.exists()
        assert hist.exists() and "CORRUPT" not in hist.read_text()
        assert [t["content"] for t in llm_chat.load_history(session="s2")] == ["u2", "a2"]
        assert llm_chat.load_history(session="s1") == []
        for s in ("s1", "s2", "default"):
            assert all("CORRUPT" not in t["content"] for t in llm_chat.load_history(session=s))

    def test_writes_fsync_and_rewrite_uses_os_replace(self, tmp_path, monkeypatch):
        """Tutor: durable writes (flush + fsync) and atomic rename.

        Real: ``append_history`` fsyncs after each pair; ``archive_history`` → ``_atomic_rewrite``
        fsyncs the ``.tmp`` and swaps it in with ``os.replace`` (archive file first, then live file).
        """
        hist = tmp_path / "llm_history.jsonl"
        monkeypatch.setenv("LLM_HISTORY_PATH", str(hist))
        fsyncs, replaces = [], []
        real_fsync, real_replace = llm_chat.os.fsync, llm_chat.os.replace
        monkeypatch.setattr(llm_chat.os, "fsync", lambda fd: (fsyncs.append(fd), real_fsync(fd))[1])
        monkeypatch.setattr(llm_chat.os, "replace",
                            lambda a, b: (replaces.append((Path(a).name, Path(b).name)), real_replace(a, b))[1])
        llm_chat.append_history("u1", "a1", session="s1")
        llm_chat.append_history("u2", "a2", session="s2")
        assert len(fsyncs) == 2 and replaces == []
        dest = llm_chat.archive_history(session="s1")
        assert dest is not None
        assert len(fsyncs) == 4  # archive .tmp + live .tmp
        assert replaces == [(dest.name + ".tmp", dest.name), (hist.name + ".tmp", hist.name)]
        assert not hist.with_name(hist.name + ".tmp").exists()

    def test_lock_serializes_history_io(self, tmp_path, monkeypatch):
        """Tutor: lock around history reads/writes.

        Real: ``_HISTORY_LOCK`` (threading.Lock) — an append waits while the lock is held.
        """
        hist = tmp_path / "llm_history.jsonl"
        monkeypatch.setenv("LLM_HISTORY_PATH", str(hist))
        done = threading.Event()

        def writer() -> None:
            llm_chat.append_history("locked-u", "locked-a", session="lk")
            done.set()

        with llm_chat._HISTORY_LOCK:
            t = threading.Thread(target=writer)
            t.start()
            assert not done.wait(0.3), "append must block while the history lock is held"
            assert not hist.exists()
        t.join(5)
        assert done.is_set()
        assert [x["content"] for x in llm_chat.load_history(session="lk")] == ["locked-u", "locked-a"]

    def test_concurrent_appends_lose_no_rows(self, tmp_path, monkeypatch):
        """Tutor: thread-safe HistoryManager.

        Real: 8 threads × 20 appends under ``_HISTORY_LOCK`` — no lost or interleaved rows.
        """
        hist = tmp_path / "llm_history.jsonl"
        monkeypatch.setenv("LLM_HISTORY_PATH", str(hist))
        n_threads, n_each = 8, 20

        def worker(i: int) -> None:
            for j in range(n_each):
                llm_chat.append_history(f"u-{i}-{j}", f"a-{i}-{j}", session=f"s{i}")

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(n_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        rows = [json.loads(x) for x in hist.read_text().splitlines() if x.strip()]
        assert len(rows) == n_threads * n_each * 2
        for i in range(n_threads):
            turns = llm_chat.load_history(session=f"s{i}")
            assert len(turns) == n_each * 2
            assert turns[0]["content"] == f"u-{i}-0"
            assert turns[-1]["content"] == f"a-{i}-{n_each - 1}"

    def test_websocket_session_query_param(self, stub_llm):
        """Tutor: HTTP ``/llm`` route with a session parameter (no such route here).

        Real: ``/cli?session=<id>`` on the WebSocket in ``cli_loopback.py``; invalid ids → ``default``.
        """
        from fastapi.testclient import TestClient

        client = TestClient(create_app())
        with client.websocket_connect("/cli?session=room42") as ws:
            banner = [ws.receive_text() for _ in range(6)]
            assert any("llm session: room42" in b for b in banner)
            ws.send_text("/llm hello from room42")
            got = []
            while not any(x.startswith("[Engine] llm:") for x in got):
                got.append(ws.receive_text())
            assert any("llm session: room42" in x for x in got)
        with client.websocket_connect("/cli?session=bad/id") as ws:
            banner = [ws.receive_text() for _ in range(6)]
            assert any("llm session: default" in b for b in banner)

    def test_deepinfer_primary_and_gguf_fallback_share_session(self, stub_llm, tmp_path, monkeypatch):
        """DeepInfer primary (127.0.0.1:8090), DeepSeek tutor secondary; one session history.

        Real: ``handle_llm_sync(session=)`` → ``complete_routed`` (llm_backend) → ``append_history``.
        Turn 1 is answered by DeepInfer (probe stubbed online); turn 2 by the ClarkeYoursaTee GGUF
        fallback (deepseek-r2 on 8085 in production) after DeepInfer goes offline. Both turns land
        in the same session and the fallback sees turn 1 as context. Loopback stub only.
        """
        from src import llm_backend

        hist = tmp_path / "llm_history.jsonl"
        url = os.environ["LLM_URL"]  # the stub_llm loopback server
        monkeypatch.setenv("LLM_HISTORY_PATH", str(hist))
        monkeypatch.setenv("LLM_RAW_REPLY", "1")
        monkeypatch.setenv("LLM_BACKEND", "deepinfer")
        monkeypatch.setenv("DEEPINFER_URL", url)
        monkeypatch.setenv("LLM_FALLBACK", "clarkeyoursatee")
        monkeypatch.setenv("LLM_CLARKEYOURSATEE_URL", url)
        monkeypatch.setenv("LLM_CLARKEYOURSATEE_MODEL", "deepseek-r2-1.5b")

        monkeypatch.setattr(llm_backend, "probe_server", lambda u, timeout=None: (True, "GET /health 200"))
        monkeypatch.setattr(stub_llm, "reply", "DeepInfer says APPLE.")
        lines1 = llm_chat.handle_llm_sync("/llm remember APPLE", session="tutor")
        assert any(x.startswith("[System] llm route: backend=deepinfer ") for x in lines1)
        assert "[System] llm order: primary=deepinfer answered" in lines1
        assert stub_llm.requests[-1]["body"]["model"] == "deepinfer"

        llm_backend.reset_state()
        monkeypatch.setattr(llm_backend, "probe_server", lambda u, timeout=None: (False, "connect refused"))
        monkeypatch.setattr(stub_llm, "reply", "Fallback recalls APPLE.")
        lines2 = llm_chat.handle_llm_sync("/llm what did I ask you to remember?", session="tutor")
        assert any(x.startswith("[System] llm: deepinfer backend offline (") for x in lines2)
        assert any("clarkeyoursatee fallback from deepinfer" in x for x in lines2)
        assert ("[System] llm order: primary=deepinfer offline → secondary: deepseek tutor "
                "(deepseek-r2-1.5b) answered") in lines2
        # DeepInfer is always tried first: the offline note precedes the secondary's order line.
        i_off = next(i for i, x in enumerate(lines2) if x.startswith("[System] llm: deepinfer backend offline ("))
        i_ord = next(i for i, x in enumerate(lines2) if x.startswith("[System] llm order:"))
        assert i_off < i_ord
        body = stub_llm.requests[-1]["body"]
        assert body["model"] == "deepseek-r2-1.5b"
        prior = [m["content"] for m in body["messages"][1:-1]]
        assert prior == ["remember APPLE", "DeepInfer says APPLE."]

        rows = [json.loads(x) for x in hist.read_text().splitlines() if x.strip()]
        assert len(rows) == 4 and {r["session"] for r in rows} == {"tutor"}
        assert [t["content"] for t in llm_chat.load_history(session="tutor")][::2] == [
            "remember APPLE", "what did I ask you to remember?"]
        assert llm_chat.load_history(session="default") == []

    def test_order_label_never_claims_tutor_for_non_deepseek_model(self, monkeypatch):
        """Provenance: the secondary is only called "deepseek tutor" when the configured model is deepseek."""
        meta = {"backend": "clarkeyoursatee", "fallback_from": "deepinfer", "deepinfer_offline": "x"}
        monkeypatch.setenv("LLM_CLARKEYOURSATEE_MODEL", "clarkeyoursatee")
        assert llm_chat.backend_order_line(meta).endswith("secondary: clarkeyoursatee (clarkeyoursatee) answered")
        monkeypatch.setenv("LLM_CLARKEYOURSATEE_MODEL", "deepseek-r2-1.5b")
        assert llm_chat.backend_order_line(meta).endswith("secondary: deepseek tutor (deepseek-r2-1.5b) answered")
        assert llm_chat.backend_order_line({"backend": "gguf"}) is None  # LLM_BACKEND=gguf: no order line
