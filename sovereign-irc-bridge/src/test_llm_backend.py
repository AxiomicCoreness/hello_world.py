"""Backend switch: DeepInfer default, offline line, labeled fallbacks, fast fail (no external network).

The only sockets used are loopback ones opened by these tests (a stub chat server
and a refused port); nothing reaches a real model server.
"""
from __future__ import annotations

import json
import socket
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from src import chatml_prebuild, llm_backend, llm_chat

WIRE = "/llm what is the brain doing?"
DS_TPL = "{% for m in messages %}<｜User｜>{{ m.content }}<｜Assistant｜>{% endfor %}"


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class _Chat(BaseHTTPRequestHandler):
    """A loopback OpenAI-style chat stub; /props returns whatever template the test sets."""
    reply = "Lane L3 is busiest."
    template = "{% for m in messages %}<|im_start|>{{ m.role }}{% endfor %}"
    posts: list = []

    def do_POST(self):  # noqa: N802
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        type(self).posts.append({"path": self.path, "body": body})
        out = json.dumps({"choices": [{"message": {"content": type(self).reply}, "finish_reason": "stop"}]})
        self._send(200, out)

    def do_GET(self):  # noqa: N802
        if self.path == "/props":
            self._send(200, json.dumps({"chat_template": type(self).template}))
        else:
            self._send(404, "{}")

    def _send(self, code, out):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(out.encode())

    def log_message(self, *a):
        pass


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    for k in ("LLM_BACKEND", "LLM_FALLBACK", "DEEPINFER_URL", "LLM_DEEPSEEK_URL", "LLM_URL", "LLM_ABLITERATED_URL",
              "DEEPINFER_REPROBE_S", "DEEPINFER_CONNECT_TIMEOUT", "LLM_PROMPT_MODE"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv("LLM_BUILD_FEEDBACK", "0")
    # DeepInfer always points at a refused loopback port: no real server is ever contacted.
    monkeypatch.setenv("DEEPINFER_URL", f"http://127.0.0.1:{_free_port()}/v1/chat/completions")
    llm_backend.reset_state()
    chatml_prebuild._PREBUILD_CHECK.clear()
    yield
    llm_backend.reset_state()
    chatml_prebuild._PREBUILD_CHECK.clear()


@pytest.fixture()
def chat_stub():
    _Chat.posts = []
    _Chat.reply = "Lane L3 is busiest."
    srv = HTTPServer(("127.0.0.1", 0), _Chat)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield _Chat, f"http://127.0.0.1:{srv.server_port}/v1/chat/completions"
    srv.shutdown()
    srv.server_close()


# ---------------------------------------------------------------- config

def test_default_backend_is_deepinfer():
    assert llm_backend.backend() == "deepinfer"
    assert llm_backend.DEFAULT_DEEPINFER_URL == "http://127.0.0.1:8090/v1/chat/completions"
    assert llm_backend.DEFAULT_DEEPSEEK_URL == "http://127.0.0.1:8082/v1/chat/completions"
    assert llm_backend.fallback() == ""
    assert llm_backend.DEFAULT_ABLITERATED_URL == "http://127.0.0.1:8083/v1/chat/completions"


def test_unknown_backend_and_fallback_rejected():
    with pytest.raises(llm_backend.BackendConfigError):
        llm_backend.backend("vllm")
    with pytest.raises(llm_backend.BackendConfigError):
        llm_backend.fallback("deepinfer")
    assert llm_backend.fallback("deepseek-fixture") == "deepseek-fixture"
    assert llm_backend.fallback("gguf-abliterated") == "gguf-abliterated"
    assert llm_backend.backend("gguf-abliterated") == "gguf-abliterated"


@pytest.mark.parametrize("name,env", [("DEEPINFER_URL", "DEEPINFER_URL"), ("LLM_DEEPSEEK_URL", "LLM_DEEPSEEK_URL"),
                                      ("LLM_ABLITERATED_URL", "LLM_ABLITERATED_URL")])
def test_backend_urls_loopback_enforced(monkeypatch, name, env):
    for bad in ("http://0.0.0.0:8090/v1/chat/completions", "http://10.0.0.5:8090/x",
                "http://api.example.com/v1/chat/completions"):
        with pytest.raises(llm_chat.LlmConfigError, match=name):
            llm_chat.assert_loopback_url(bad, name)
    monkeypatch.setenv(env, "http://0.0.0.0:8090/v1/chat/completions")
    if env == "LLM_DEEPSEEK_URL":
        monkeypatch.setenv("LLM_BACKEND", "deepseek-fixture")
    if env == "LLM_ABLITERATED_URL":
        monkeypatch.setenv("LLM_BACKEND", "gguf-abliterated")
    lines = llm_chat.handle_llm_sync(WIRE)
    assert lines[-1].startswith(f"[System] llm offline: {name} must be")


def test_default_connect_timeout_is_half_second(monkeypatch):
    assert llm_backend.connect_timeout() == 0.5
    monkeypatch.setenv("DEEPINFER_CONNECT_TIMEOUT", "0.2")
    assert llm_backend.connect_timeout() == 0.2


# ---------------------------------------------------------------- capability probe

def test_capability_probe_with_find_spec_monkeypatched():
    present = {"torch", "deep_gemm"}
    caps = llm_backend.capabilities(find_spec=lambda n: object() if n in present else None,
                                    cuda_check=lambda: False)
    assert caps == {"deep_gemm": True, "deep_ep": False, "flash_mla": False, "torch": True,
                    "deepinfer._C": False, "cuda": False}
    summary = llm_backend.capability_summary(caps)
    assert "deep_gemm present" in summary and "deep_ep missing" in summary and summary.endswith("no CUDA")


def test_capability_probe_never_asks_cuda_without_torch():
    asked = []
    caps = llm_backend.capabilities(find_spec=lambda n: None, cuda_check=lambda: asked.append(1) or True)
    assert caps["cuda"] is False and asked == []


def test_capability_probe_tolerates_missing_parent_package():
    def find_spec(name):
        if name == "deepinfer._C":
            raise ModuleNotFoundError("No module named 'deepinfer'")
        return None

    assert llm_backend.capabilities(find_spec=find_spec, cuda_check=lambda: False)["deepinfer._C"] is False


def test_status_line_offline():
    caps = dict.fromkeys(llm_backend.CAPABILITY_MODULES, False) | {"cuda": False}
    line = llm_backend.status_line("deepinfer", "http://127.0.0.1:8090/v1/chat/completions",
                                   (False, "no server at 127.0.0.1:8090"), caps)
    assert line.startswith("[System] llm backend: deepinfer OFFLINE (no server at 127.0.0.1:8090; deep_gemm missing;")
    assert line.endswith("no CUDA)")


# ---------------------------------------------------------------- offline / fast fail / cache

def test_deepinfer_offline_message_without_fallback():
    t = time.monotonic()
    lines = llm_chat.handle_llm_sync(WIRE)
    assert time.monotonic() - t < 2.0
    assert lines[-1].startswith("[System] llm route: backend=deepinfer (offline)")
    assert any(x.startswith("[System] llm: deepinfer backend offline (no server at 127.0.0.1:") for x in lines)
    assert not any(x.startswith("[Engine]") for x in lines)


def test_offline_probe_returns_fast_on_a_blackholed_address(monkeypatch):
    """connect_ex is bounded by DEEPINFER_CONNECT_TIMEOUT (0.5 s default), not the OS socket timeout."""
    def slow_connect(self, addr):
        time.sleep(self.gettimeout() or 0)
        return 110  # ETIMEDOUT, after waiting exactly the configured timeout

    monkeypatch.setattr(socket.socket, "connect_ex", slow_connect)
    t = time.monotonic()
    ok, detail = llm_backend.probe_server("http://127.0.0.1:8090/v1/chat/completions")
    took = time.monotonic() - t
    assert not ok and "no server at 127.0.0.1:8090" in detail
    assert 0.4 <= took < 1.0


def test_offline_state_is_cached_until_reprobe():
    calls = []
    clock = [100.0]

    def probe(url):
        calls.append(url)
        return False, "no server"

    url = "http://127.0.0.1:8090/v1/chat/completions"
    for _ in range(3):
        assert llm_backend.deepinfer_state(url, now=lambda: clock[0], probe=probe) == (False, "no server")
    assert len(calls) == 1
    clock[0] += 29.0
    llm_backend.deepinfer_state(url, now=lambda: clock[0], probe=probe)
    assert len(calls) == 1
    clock[0] += 2.0
    llm_backend.deepinfer_state(url, now=lambda: clock[0], probe=probe)
    assert len(calls) == 2


# ---------------------------------------------------------------- provenance

def test_gguf_fallback_is_labeled_qwen(monkeypatch, chat_stub, caplog):
    stub, url = chat_stub
    monkeypatch.setenv("LLM_FALLBACK", "gguf")
    monkeypatch.setenv("LLM_URL", url)
    with caplog.at_level("INFO", logger="sovereign-irc-bridge.llm"):
        lines = llm_chat.handle_llm_sync(WIRE)
    assert any(x.startswith("[System] llm: deepinfer backend offline (") for x in lines)
    assert "[System] llm route: backend=qwen (gguf fallback from deepinfer) path=/v1/chat/completions mode=auto family=chatml" in lines
    engine = [x for x in lines if x.startswith("[Engine]")]
    assert engine == ["[Engine] llm: [Fallback: Qwen] Lane L3 is busiest."]
    assert not any("backend=deepinfer" in x for x in lines)
    assert llm_backend.FALLBACK_LOG in caplog.text
    rec = [json.loads(r.getMessage().split(" ", 1)[1]) for r in caplog.records if r.getMessage().startswith("llm_reply ")]
    assert rec[-1]["backend"] == "qwen" and rec[-1]["fallback_from"] == "deepinfer"
    _, err, meta = llm_chat.complete_routed([{"role": "user", "content": "x"}])
    assert err is None and meta["backend"] == "qwen"


def test_gguf_abliterated_fallback_is_labeled(monkeypatch, chat_stub, caplog):
    stub, url = chat_stub
    monkeypatch.setenv("LLM_FALLBACK", "gguf-abliterated")
    monkeypatch.setenv("LLM_ABLITERATED_URL", url)
    # Plain Qwen points at a dead port: the abliterated server must be the one answering.
    monkeypatch.setenv("LLM_URL", f"http://127.0.0.1:{_free_port()}/v1/chat/completions")
    with caplog.at_level("INFO", logger="sovereign-irc-bridge.llm"):
        lines = llm_chat.handle_llm_sync(WIRE)
    assert any(x.startswith("[System] llm: deepinfer backend offline (") for x in lines)
    assert ("[System] llm route: backend=qwen-abliterated (gguf-abliterated fallback from deepinfer) "
            "path=/v1/chat/completions mode=auto family=chatml") in lines
    engine = [x for x in lines if x.startswith("[Engine]")]
    assert engine == ["[Engine] llm: [Fallback: Qwen2.5-1.5B abliterated] Lane L3 is busiest."]
    assert not any("backend=deepinfer" in x or "backend=qwen " in x for x in lines)
    assert not any("[Fallback: Qwen] " in x for x in lines)
    assert llm_backend.ABLITERATED_FALLBACK_LOG in caplog.text
    rec = [json.loads(r.getMessage().split(" ", 1)[1]) for r in caplog.records if r.getMessage().startswith("llm_reply ")]
    assert rec[-1]["backend"] == "qwen-abliterated" and rec[-1]["fallback_from"] == "deepinfer"
    body = stub.posts[-1]["body"]
    assert body["model"] == "qwen2.5-1.5b-instruct-abliterated"
    assert "<|im_end|>" in body["stop"]
    _, err, meta = llm_chat.complete_routed([{"role": "user", "content": "x"}])
    assert err is None and meta["backend"] == "qwen-abliterated"


def test_gguf_abliterated_backend_direct_is_labeled(monkeypatch, chat_stub, caplog):
    stub, url = chat_stub
    monkeypatch.setenv("LLM_BACKEND", "gguf-abliterated")
    monkeypatch.setenv("LLM_ABLITERATED_URL", url)
    with caplog.at_level("INFO", logger="sovereign-irc-bridge.llm"):
        lines = llm_chat.handle_llm_sync(WIRE)
    assert "[System] llm route: backend=qwen-abliterated path=/v1/chat/completions mode=auto family=chatml" in lines
    assert [x for x in lines if x.startswith("[Engine]")] == [
        "[Engine] llm: [Fallback: Qwen2.5-1.5B abliterated] Lane L3 is busiest."]
    assert not any("deepinfer" in x.lower() for x in lines)
    rec = [json.loads(r.getMessage().split(" ", 1)[1]) for r in caplog.records if r.getMessage().startswith("llm_reply ")]
    assert rec[-1]["backend"] == "qwen-abliterated" and rec[-1]["fallback_from"] is None


def test_gguf_abliterated_startup_and_health(monkeypatch):
    monkeypatch.setenv("LLM_FALLBACK", "gguf-abliterated")
    line = llm_backend.startup_probe("http://127.0.0.1:8081/v1/chat/completions")
    assert "deepinfer OFFLINE" in line
    assert line.endswith("→ fallback gguf-abliterated (Qwen2.5-1.5B abliterated at 127.0.0.1:8083)")
    blob = llm_backend.health_blob()
    assert blob["fallback"] == "gguf-abliterated"
    assert blob["abliterated_url"] == "http://127.0.0.1:8083/v1/chat/completions"
    assert llm_backend.reply_prefix("qwen-abliterated") == "[Fallback: Qwen2.5-1.5B abliterated] "
    assert llm_backend.reply_prefix("qwen-abliterated") != llm_backend.reply_prefix("qwen")


def test_deepseek_fixture_backend_labeled_and_template(monkeypatch, chat_stub, caplog):
    stub, url = chat_stub
    stub.template = DS_TPL
    stub.reply = "</think>Clouds are pillows.<｜User｜>more"
    monkeypatch.setenv("LLM_BACKEND", "deepseek-fixture")
    monkeypatch.setenv("LLM_DEEPSEEK_URL", url)
    with caplog.at_level("INFO", logger="sovereign-irc-bridge.llm"):
        lines = llm_chat.handle_llm_sync(WIRE)
    stub.template = _Chat.template = "{% for m in messages %}<|im_start|>{{ m.role }}{% endfor %}"
    assert "[System] llm route: backend=deepseek-fixture path=/v1/chat/completions mode=auto family=deepseek" in lines
    assert [x for x in lines if x.startswith("[Engine]")] == [
        "[Engine] llm: [DeepSeek-V4 fixture: RalphSeek 122M — not a real model] Clouds are pillows."]
    body = stub.posts[-1]["body"]
    assert body["chat_template_kwargs"] == {"enable_thinking": False}
    assert "<｜end▁of▁sentence｜>" in body["stop"] and "<｜User｜>" in body["stop"]
    assert body["model"] == "ralphseek-v4-flash"
    assert not any("deepinfer" in x.lower() for x in lines)
    rec = [json.loads(r.getMessage().split(" ", 1)[1]) for r in caplog.records if r.getMessage().startswith("llm_reply ")]
    assert rec[-1]["backend"] == "deepseek-fixture" and rec[-1]["fallback_from"] is None


def test_deepseek_fixture_fallback_from_deepinfer(monkeypatch, chat_stub, caplog):
    stub, url = chat_stub
    stub.template = DS_TPL
    monkeypatch.setenv("LLM_FALLBACK", "deepseek-fixture")
    monkeypatch.setenv("LLM_DEEPSEEK_URL", url)
    with caplog.at_level("WARNING", logger="sovereign-irc-bridge.llm"):
        lines = llm_chat.handle_llm_sync(WIRE)
    stub.template = _Chat.template = "{% for m in messages %}<|im_start|>{{ m.role }}{% endfor %}"
    assert any(x.startswith("[System] llm: deepinfer backend offline (") for x in lines)
    assert any(x.startswith("[System] llm route: backend=deepseek-fixture (fixture fallback from deepinfer)") for x in lines)
    assert [x for x in lines if x.startswith("[Engine]")] == [
        "[Engine] llm: [DeepSeek-V4 fixture: RalphSeek 122M — not a real model] Lane L3 is busiest."]
    assert llm_backend.FIXTURE_FALLBACK_LOG in caplog.text


def test_deepinfer_online_reply_labeled_deepinfer(monkeypatch, chat_stub):
    stub, url = chat_stub
    monkeypatch.setenv("DEEPINFER_URL", url)
    monkeypatch.setenv("LLM_FALLBACK", "gguf")
    monkeypatch.setattr(llm_backend, "probe_server", lambda u, timeout=None: (True, "GET /health 200"))
    lines = llm_chat.handle_llm_sync(WIRE)
    assert "[System] llm route: backend=deepinfer path=/v1/chat/completions mode=auto family=chatml" in lines
    assert [x for x in lines if x.startswith("[Engine]")] == ["[Engine] llm: Lane L3 is busiest."]
    assert not any("Fallback" in x or "fixture" in x for x in lines)
    assert stub.posts[-1]["body"]["model"] == "deepinfer"


def test_deepseek_family_and_stops():
    assert chatml_prebuild.template_family(DS_TPL) == "deepseek"
    stops = chatml_prebuild.stops_for("deepseek")
    assert stops[:3] == ["<｜end▁of▁sentence｜>", "<｜User｜>", "<｜Assistant｜>"]
    assert "User 1:" in stops


def test_clean_reply_cuts_deepseek_turn_and_think_tags():
    text, notes = llm_chat.clean_reply("</think>Clouds are pillows.\n<｜User｜>Tell me more<｜Assistant｜>")
    assert text == "Clouds are pillows." and len(notes) == 1
    assert llm_chat.clean_reply("A normal reply.") == ("A normal reply.", [])
