"""chatml_prebuild: routing, rendering, stops, tokenization gate, degenerate guard (no network)."""
from __future__ import annotations

import pytest

from src import chatml_prebuild as cp

BASE = "http://127.0.0.1:8081"
MSGS = [{"role": "system", "content": "S"}, {"role": "user", "content": "U"}]
CHATML_TPL = "{% for m in messages %}<|im_start|>{{ m.role }}\n{{ m.content }}<|im_end|>\n{% endfor %}"


@pytest.fixture(autouse=True)
def _no_network(monkeypatch):
    def boom(*a, **k):
        raise AssertionError("network used in a unit test")

    monkeypatch.setattr(cp, "_get_json", boom)
    monkeypatch.setattr(cp, "_post_json", boom)
    cp._PREBUILD_CHECK.clear()
    monkeypatch.delenv("LLM_PROMPT_MODE", raising=False)
    yield
    cp._PREBUILD_CHECK.clear()


def test_render_chatml_exact():
    assert cp.render_chatml(MSGS) == (
        "<|im_start|>system\nS<|im_end|>\n<|im_start|>user\nU<|im_end|>\n<|im_start|>assistant\n"
    )
    assert cp.render_chatml([{"role": "user", "content": "U"}], add_generation_prompt=False) == (
        "<|im_start|>system\nYou are a helpful assistant.<|im_end|>\n<|im_start|>user\nU<|im_end|>\n"
    )


def test_template_family_detection():
    assert cp.template_family(CHATML_TPL) == "chatml"
    assert cp.template_family("{{ '<|start_header_id|>' + role }}<|eot_id|>") == "llama3"
    assert cp.template_family("<start_of_turn>user\n{{ c }}<end_of_turn>") == "gemma"
    assert cp.template_family("{{ messages }}") == "unknown"
    assert cp.template_family("") == "none" and cp.template_family(None) == "none"
    assert cp.template_family("   \n") == "none"


def test_auto_picks_chat_when_template_present(monkeypatch):
    monkeypatch.setattr(cp, "probe_props", lambda b, timeout=3.0: {"chat_template": CHATML_TPL})
    path, payload, meta = cp.build_request(MSGS, BASE, "auto", prebuild_ok=(True, "ok"))
    assert path == "/v1/chat/completions" and meta["path"] == path
    assert meta["family"] == "chatml" and meta["reason"] == "server template"
    assert payload["messages"] == MSGS and "prompt" not in payload
    assert payload["repeat_penalty"] == 1.1 and payload["repeat_last_n"] == 256


@pytest.mark.parametrize("props", [None, {"chat_template": ""}, {}])
def test_auto_picks_prebuild_when_template_empty_or_probe_fails(monkeypatch, props):
    monkeypatch.setattr(cp, "probe_props", lambda b, timeout=3.0: props)
    path, payload, meta = cp.build_request(MSGS, BASE, "auto", prebuild_ok=(True, "ok"))
    assert path == "/completion" and meta["path"] == "/completion" and meta["reason"] == "no chat_template"
    assert payload["prompt"] == cp.render_chatml(MSGS) and "messages" not in payload
    assert payload["prompt"].endswith("<|im_start|>assistant\n")
    assert payload["repeat_penalty"] == 1.1 and payload["repeat_last_n"] == 256


def test_forced_modes(monkeypatch):
    monkeypatch.setattr(cp, "probe_props", lambda b, timeout=3.0: {"chat_template": CHATML_TPL})
    path, _, meta = cp.build_request(MSGS, BASE, "prebuild", prebuild_ok=(True, "ok"))
    assert path == "/completion" and meta["reason"] == "forced"
    monkeypatch.setattr(cp, "probe_props", lambda b, timeout=3.0: None)
    path, _, meta = cp.build_request(MSGS, BASE, "chat", prebuild_ok=(True, "ok"))
    assert path == "/v1/chat/completions" and meta["reason"] == "forced chat"
    monkeypatch.setenv("LLM_PROMPT_MODE", "PREBUILD")
    assert cp.prompt_mode() == "prebuild"
    with pytest.raises(cp.PromptConfigError):
        cp.prompt_mode("raw")


def test_stop_sets_shared_and_merged_with_role_echo():
    chatml = cp.stops_for("chatml")
    for s in ("<|im_end|>", "<|im_start|>", "\nUser:", "\nuser:", "\nHuman:", "User 1:"):
        assert s in chatml
    assert "<|eot_id|>" in cp.stops_for("llama3") and "<|start_header_id|>" in cp.stops_for("llama3")
    assert "<end_of_turn>" in cp.stops_for("gemma") and "<start_of_turn>" in cp.stops_for("gemma")
    for fam in ("unknown", "none", "nonsense"):
        assert "User 1:" in cp.stops_for(fam)
    assert len(chatml) == len(set(chatml))


def test_both_routes_use_the_family_stops(monkeypatch):
    monkeypatch.setattr(cp, "probe_props", lambda b, timeout=3.0: {"chat_template": CHATML_TPL})
    _, chat, _ = cp.build_request(MSGS, BASE, "chat", prebuild_ok=(True, "ok"))
    _, pre, _ = cp.build_request(MSGS, BASE, "prebuild", prebuild_ok=(True, "ok"))
    assert chat["stop"] == pre["stop"] == cp.stops_for("chatml")


def test_tokenization_gate_disables_prebuild(monkeypatch, caplog):
    monkeypatch.setattr(cp, "probe_props", lambda b, timeout=3.0: None)
    monkeypatch.setattr(cp, "tokenize", lambda b, t, timeout=3.0: [27, 91, 318, 5011] if "start" in t else [151645])
    ok, detail = cp.verify_prebuild_tokenization(BASE)
    assert not ok and "<|im_start|> -> 4 tokens" in detail
    with caplog.at_level("ERROR"):
        path, payload, meta = cp.build_request(MSGS, BASE, "auto")
    assert path == "/v1/chat/completions" and "messages" in payload
    assert meta["reason"] == "prebuild unavailable" and "4 tokens" in meta["prebuild_disabled"]
    assert any("prebuild DISABLED" in r.message for r in caplog.records)
    # forced prebuild also falls back to chat instead of sending markers as text
    path, _, meta = cp.build_request(MSGS, BASE, "prebuild")
    assert path == "/v1/chat/completions" and "prebuild_disabled" in meta


def test_tokenization_ok_and_failed_probe(monkeypatch):
    monkeypatch.setattr(cp, "tokenize", lambda b, t, timeout=3.0: [151644] if "start" in t else [151645])
    assert cp.verify_prebuild_tokenization(BASE) == (True, "single ids <|im_start|>=151644 <|im_end|>=151645")
    monkeypatch.setattr(cp, "tokenize", lambda b, t, timeout=3.0: None)
    ok, detail = cp.verify_prebuild_tokenization(BASE)
    assert not ok and "failed" in detail


def test_startup_check_never_raises(monkeypatch):
    monkeypatch.setattr(cp, "probe_props", lambda b, timeout=3.0: (_ for _ in ()).throw(RuntimeError("x")))
    cp.startup_check("http://127.0.0.1:8081/v1/chat/completions")  # logs, no exception


def test_base_url_loopback_only():
    assert cp.base_url("http://127.0.0.1:8081/v1/chat/completions") == "http://127.0.0.1:8081"
    assert cp.base_url("http://localhost:8081") == "http://localhost:8081"
    for bad in ("http://0.0.0.0:8081/v1/chat/completions", "http://10.0.0.2:8081", "ftp://127.0.0.1:8081"):
        with pytest.raises(cp.PromptConfigError):
            cp.base_url(bad)


def test_extract_text_and_finish_reason():
    chat = {"choices": [{"message": {"content": "hi"}, "finish_reason": "stop"}]}
    comp = {"content": "yo", "stopped_word": True, "stopping_word": "<|im_end|>"}
    assert cp.extract_text(chat) == "hi" and cp.finish_reason(chat) == "stop"
    assert cp.extract_text(comp) == "yo" and cp.finish_reason(comp) == "stop:<|im_end|>"
    assert cp.extract_text({"x": 1}) is None and cp.extract_text("nope") is None


def test_degenerate_guard():
    loop = "The lanes are quiet. " + "They are just sitting in a dark room. " * 9
    assert cp.looks_degenerate(loop)
    out, cut = cp.truncate_degenerate(loop)
    assert cut and out.strip() == "The lanes are quiet. They are just sitting in a dark room."
    normal = "Lobula is busiest with 7 spikes; antennal lobe 4, lateral horn 5, mushroom body 3."
    assert not cp.looks_degenerate(normal) and cp.truncate_degenerate(normal) == (normal, False)
    assert not cp.looks_degenerate("a b c " * 4)  # 4 copies is the limit, not over it
