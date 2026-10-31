# SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
# SPDX-License-Identifier: MIT
"""Offline tests for serving/bench_llm.py: SSE parsing, per-prompt summary, markdown.

No network and no llama-server: a fake SSE stream shaped like llama-server's
/v1/chat/completions output and a fake clock. Runs under pytest or directly:
    python -I sovereign-irc-bridge/src/test_bench_llm.py
"""
from __future__ import annotations

import importlib.util
import json
import sys
from datetime import datetime
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "serving" / "bench_llm.py"
_spec = importlib.util.spec_from_file_location("bench_llm_under_test", SCRIPT)
bench = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = bench
_spec.loader.exec_module(bench)


def _chunk(delta=None, finish=None, **extra) -> str:
    obj = {"choices": [{"index": 0, "delta": delta or {}, "finish_reason": finish}],
           "object": "chat.completion.chunk", "system_fingerprint": "b12015-deadbee"}
    obj.update(extra)
    return "data: " + json.dumps(obj) + "\n"


TIMINGS = {"cache_n": 0, "prompt_n": 14, "prompt_ms": 70.0, "prompt_per_second": 200.0,
           "predicted_n": 5, "predicted_ms": 250.0, "predicted_per_second": 20.0}


def fake_stream() -> list[bytes]:
    lines = [
        ": keep-alive comment\n", "\n",
        _chunk({"role": "assistant", "content": None}), "\n",          # role-only chunk: not a token
        _chunk({"reasoning_content": "phi solves x^2=x+1"}), "\r\n",    # first token (thinking), CRLF
        _chunk({"content": "The golden ratio is "}), "\n",
        _chunk({"content": "\\(\\varphi\\)"}), "\n",
        "data: {not json\n", "\n",                                      # ignored garbage
        _chunk({}, finish="stop"), "\n",
        "data: " + json.dumps({"choices": [], "usage": {"completion_tokens": 5, "prompt_tokens": 14,
                                                       "total_tokens": 19}, "timings": TIMINGS}) + "\n", "\n",
        "data: [DONE]\n", "\n",
        _chunk({"content": "after done, must be ignored"}), "\n",
    ]
    return [s.encode() for s in lines]


class FakeClock:
    """Each call advances: start=100.0, then one tick per data event."""

    def __init__(self, ticks):
        self.ticks = list(ticks)

    def __call__(self):
        return self.ticks.pop(0)


def _parsed():
    # data events in order: role, reasoning, content, content, garbage, finish, usage, [DONE]
    clock = FakeClock([100.05, 100.40, 100.50, 100.60, 100.61, 100.70, 100.71, 100.72])
    return bench.parse_stream(fake_stream(), clock=clock, t_start=100.0)


def test_iter_sse_data_multiline_and_fields():
    lines = ["event: x\n", "data: a\n", "data: b\n", "id: 1\n", "\n", "data:c\n", "retry: 5\n"]
    assert list(bench.iter_sse_data(lines)) == ["a\nb", "c"]


def test_parse_stream_text_usage_timings():
    p = _parsed()
    assert p["reasoning"] == "phi solves x^2=x+1"
    assert p["content"] == "The golden ratio is \\(\\varphi\\)"
    assert "after done" not in p["content"] and p["done"] is True
    assert p["finish_reason"] == "stop"
    assert p["usage"]["completion_tokens"] == 5
    assert p["timings"]["predicted_per_second"] == 20.0
    assert p["system_fingerprint"] == "b12015-deadbee"
    assert p["t_first"] == 100.40  # first reasoning token, not the role-only chunk
    assert p["t_end"] == 100.72


def test_summarize_numbers():
    r = bench.summarize("golden_ratio", _parsed())
    assert r["id"] == "golden_ratio"
    assert r["ttft_s"] == 0.4
    assert r["total_s"] == 0.72
    assert r["completion_tokens"] == 5 and r["prompt_tokens"] == 14
    assert r["gen_tok_s"] == 20.0          # llama-server's own predicted_per_second
    assert r["prompt_tok_s"] == 200.0      # prompt eval speed
    assert r["wall_tok_s"] == round(4 / 0.32, 2)   # tokens after the first / time after the first
    assert r["overall_tok_s"] == round(5 / 0.72, 2)
    assert r["finish_reason"] == "stop" and r["has_usage"] and r["has_timings"]


def test_summarize_falls_back_to_timings_without_usage():
    p = _parsed()
    p["usage"] = {}
    r = bench.summarize("x", p)
    assert r["completion_tokens"] == 5 and r["prompt_tokens"] == 14 and r["has_usage"] is False


def test_summarize_empty_stream_is_safe():
    p = bench.parse_stream([b"data: [DONE]\n", b"\n"], clock=lambda: 1.0, t_start=1.0)
    r = bench.summarize("empty", p)
    assert r["ttft_s"] is None and r["completion_tokens"] is None and r["gen_tok_s"] is None


def test_server_error_in_stream_raises():
    try:
        bench.parse_stream([b'data: {"error": {"message": "boom"}}\n', b"\n"], clock=lambda: 0.0)
    except RuntimeError as e:
        assert "boom" in str(e)
    else:
        raise AssertionError("expected RuntimeError")


def _report():
    ok = bench.summarize("golden_ratio", _parsed())
    results = [ok, {"id": "add_2_3", "error": "URLError: refused"}]
    return {
        "timestamp": "2026-10-31T09:43:00-04:00",
        "params": {"seed": 42, "temperature": 0},
        "runner": {"cpu_model": "Fake CPU", "cpu_cores": 4, "ram_gb": 15.6,
                   "llama_build": "b12015", "model_sha256": "80a4" + "0" * 60},
        "results": results,
        "aggregate": bench.aggregate(results),
        "reference": bench.REFERENCE,
    }


def test_aggregate_counts_failures():
    agg = _report()["aggregate"]
    assert agg == {"prompts_ok": 1, "prompts_failed": 1, "completion_tokens": 5,
                   "gen_tok_s": 20.0, "overall_tok_s": round(5 / 0.72, 2), "mean_ttft_s": 0.4}


def test_markdown_table():
    md = bench.markdown_table(_report())
    assert md.startswith("### LLM bench")
    assert "| Prompt | TTFT (s) | Tokens | tok/s (server) | tok/s (wall) | Prompt eval tok/s | Finish |" in md
    assert "| `golden_ratio` | 0.4 | 5 | 20.0 | 12.5 | 200.0 | stop |" in md
    assert "| `add_2_3` | – |" in md and "error: URLError: refused" in md
    assert "**16.8 tok/s**" in md and "**20.0 tok/s** (1.19× the box)" in md
    assert "b12015" in md and "Fake CPU (4 cores, 15.6 GB RAM)" in md


def test_reference_and_prompts_pinned():
    ids = [p["id"] for p in bench.PROMPTS]
    assert ids[0] == "golden_ratio" and len(ids) == len(set(ids))
    assert bench.PROMPTS[0]["prompt"] == "What is the golden ratio? Use LaTeX."
    assert bench.REFERENCE["completion_tokens"] == 597 and bench.REFERENCE["tok_s"] == 16.8


def test_timestamp_is_iso8601_new_york():
    ts = bench.now_iso_new_york()
    off = datetime.fromisoformat(ts).utcoffset()
    assert off is not None and off.total_seconds() in (-4 * 3600, -5 * 3600)  # EDT / EST


def test_runner_info_shape():
    info = bench.runner_info("ab" * 32, "b12015")
    assert info["model_sha256"] == "ab" * 32 and info["llama_build"] == "b12015"
    assert isinstance(info["cpu_cores"], int) and info["cpu_cores"] >= 1


if __name__ == "__main__":
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    for name, fn in tests:
        fn()
        print("ok", name)
    print(f"{len(tests)} passed")
