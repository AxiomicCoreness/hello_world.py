#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
# SPDX-License-Identifier: MIT
"""bench_llm.py — throughput benchmark for the pinned deepseek-r2 model on llama-server.

Stdlib only. Sends a fixed set of prompts to an OpenAI-compatible llama-server
(default http://127.0.0.1:8085) with a fixed seed and temperature 0, streaming,
and records per prompt:

  * ttft_s              wall-clock time to the first streamed token (thinking or answer)
  * completion_tokens   from the server's ``usage`` (falls back to ``timings.predicted_n``)
  * gen_tok_s           llama-server's own ``timings.predicted_per_second``
  * wall_tok_s          completion tokens / wall-clock seconds from first token to the end
  * prompt_tok_s        llama-server's ``timings.prompt_per_second`` (prompt eval speed)

Writes bench.json (with runner info: CPU model, cores, RAM, llama.cpp build, model sha256,
ISO 8601 timestamp in America/New_York) and appends a markdown table to
$GITHUB_STEP_SUMMARY when that variable is set.

Reference: on the bot's box (llama.cpp b11840, CPU) the golden-ratio prompt produced
597 tokens in 35.7 s = 16.8 tok/s (2026-10-30). ``REFERENCE`` below records that.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable, Iterator

SCHEMA = "bench_llm/v1"
DEFAULT_URL = "http://127.0.0.1:8085"
DEFAULT_MODEL = "deepseek-r2-1.5b"
DEFAULT_SEED = 42
DEFAULT_MAX_TOKENS = 1024

# Fixed prompt set. Ids are stable so runs can be compared week to week.
PROMPTS: list[dict[str, str]] = [
    {"id": "golden_ratio", "prompt": "What is the golden ratio? Use LaTeX."},
    {"id": "add_2_3", "prompt": "What is 2+3? Answer briefly."},
    {"id": "fib_python", "prompt": "Write a Python function that returns the n-th Fibonacci number."},
]

# The measurement this benchmark was wired up from (bot's box, 2026-10-30, America/New_York).
REFERENCE = {
    "where": "Grok Bot box (CPU), llama.cpp b11840, deepseek-r2-1.5b Q4_K_M",
    "prompt_id": "golden_ratio",
    "completion_tokens": 597,
    "seconds": 35.7,
    "tok_s": 16.8,
    "date": "2026-10-30",
}


# --------------------------------------------------------------------------- parsing

def iter_sse_data(lines: Iterable[bytes | str]) -> Iterator[str]:
    """Yield the payload of each ``data:`` event in a server-sent-events stream.

    Handles bytes or str lines, CRLF endings, comments (``:``), other fields, and
    multi-line ``data:`` events (joined with newlines, per the SSE spec).
    """
    buf: list[str] = []
    for raw in lines:
        line = raw.decode("utf-8", "replace") if isinstance(raw, (bytes, bytearray)) else raw
        line = line.rstrip("\r\n")
        if line == "":
            if buf:
                yield "\n".join(buf)
                buf = []
            continue
        if line.startswith(":"):
            continue
        field, _, value = line.partition(":")
        if value.startswith(" "):
            value = value[1:]
        if field == "data":
            buf.append(value)
    if buf:
        yield "\n".join(buf)


def parse_stream(lines: Iterable[bytes | str], clock=time.monotonic, t_start: float | None = None) -> dict:
    """Consume an OpenAI-style chat.completion.chunk stream and measure it.

    ``clock`` is called when each chunk arrives, so tests can inject a fake clock.
    Returns a dict with text, reasoning, usage, timings, and timing points.
    """
    t0 = clock() if t_start is None else t_start
    t_first = None
    t_last = t0
    content: list[str] = []
    reasoning: list[str] = []
    usage: dict = {}
    timings: dict = {}
    finish_reason = None
    fingerprint = None
    chunks = 0
    done = False
    for data in iter_sse_data(lines):
        now = clock()
        if data.strip() == "[DONE]":
            done = True
            t_last = now
            break
        try:
            obj = json.loads(data)
        except json.JSONDecodeError:
            continue
        if not isinstance(obj, dict):
            continue
        if "error" in obj:
            raise RuntimeError(f"server error in stream: {obj['error']}")
        chunks += 1
        t_last = now
        fingerprint = obj.get("system_fingerprint") or fingerprint
        if isinstance(obj.get("usage"), dict):
            usage = obj["usage"]
        if isinstance(obj.get("timings"), dict):
            timings = obj["timings"]
        for choice in obj.get("choices") or []:
            delta = choice.get("delta") or {}
            piece_c = delta.get("content") or ""
            piece_r = delta.get("reasoning_content") or ""
            if (piece_c or piece_r) and t_first is None:
                t_first = now
            if piece_c:
                content.append(piece_c)
            if piece_r:
                reasoning.append(piece_r)
            if choice.get("finish_reason"):
                finish_reason = choice["finish_reason"]
    return {
        "content": "".join(content),
        "reasoning": "".join(reasoning),
        "usage": usage,
        "timings": timings,
        "finish_reason": finish_reason,
        "system_fingerprint": fingerprint,
        "chunks": chunks,
        "done": done,
        "t_start": t0,
        "t_first": t_first,
        "t_end": t_last,
    }


def _num(x) -> float | None:
    return float(x) if isinstance(x, (int, float)) and not isinstance(x, bool) else None


def _r(x: float | None, nd: int = 3) -> float | None:
    return None if x is None else round(x, nd)


def summarize(prompt_id: str, parsed: dict) -> dict:
    """Turn a parse_stream() result into the per-prompt bench record."""
    usage, timings = parsed.get("usage") or {}, parsed.get("timings") or {}
    completion = _num(usage.get("completion_tokens"))
    if completion is None:
        completion = _num(timings.get("predicted_n"))
    prompt_tokens = _num(usage.get("prompt_tokens"))
    if prompt_tokens is None:
        prompt_tokens = _num(timings.get("prompt_n"))
    t0, t1, tend = parsed.get("t_start"), parsed.get("t_first"), parsed.get("t_end")
    ttft = (t1 - t0) if (t0 is not None and t1 is not None) else None
    total = (tend - t0) if (t0 is not None and tend is not None) else None
    gen_wall = (tend - t1) if (t1 is not None and tend is not None) else None
    wall_tok_s = None
    if completion and gen_wall and gen_wall > 0:
        # tokens after the first one, over the time after the first one arrived
        wall_tok_s = max(completion - 1, 0) / gen_wall if completion > 1 else None
    overall_tok_s = completion / total if (completion and total and total > 0) else None
    return {
        "id": prompt_id,
        "ttft_s": _r(ttft),
        "total_s": _r(total),
        "completion_tokens": int(completion) if completion is not None else None,
        "prompt_tokens": int(prompt_tokens) if prompt_tokens is not None else None,
        "gen_tok_s": _r(_num(timings.get("predicted_per_second")), 2),
        "wall_tok_s": _r(wall_tok_s, 2),
        "overall_tok_s": _r(overall_tok_s, 2),
        "prompt_tok_s": _r(_num(timings.get("prompt_per_second")), 2),
        "prompt_ms": _r(_num(timings.get("prompt_ms")), 1),
        "predicted_ms": _r(_num(timings.get("predicted_ms")), 1),
        "cache_n": timings.get("cache_n"),
        "finish_reason": parsed.get("finish_reason"),
        "answer_chars": len(parsed.get("content") or ""),
        "thinking_chars": len(parsed.get("reasoning") or ""),
        "has_usage": bool(parsed.get("usage")),
        "has_timings": bool(timings),
    }


def aggregate(results: list[dict]) -> dict:
    """Token-weighted totals across prompts (server timings and wall clock)."""
    ok = [r for r in results if not r.get("error")]
    toks = sum(r["completion_tokens"] or 0 for r in ok)
    pred_ms = sum(r["predicted_ms"] or 0 for r in ok)
    total_s = sum(r["total_s"] or 0 for r in ok)
    ttfts = [r["ttft_s"] for r in ok if r.get("ttft_s") is not None]
    return {
        "prompts_ok": len(ok),
        "prompts_failed": len(results) - len(ok),
        "completion_tokens": toks,
        "gen_tok_s": round(toks / (pred_ms / 1000), 2) if pred_ms > 0 else None,
        "overall_tok_s": round(toks / total_s, 2) if total_s > 0 else None,
        "mean_ttft_s": round(sum(ttfts) / len(ttfts), 3) if ttfts else None,
    }


def _fmt(x, suffix: str = "") -> str:
    return "–" if x is None else f"{x}{suffix}"


def markdown_table(report: dict) -> str:
    """Markdown for $GITHUB_STEP_SUMMARY."""
    run, ref, agg = report.get("runner", {}), report.get("reference", {}), report.get("aggregate", {})
    out = [
        "### LLM bench · deepseek-r2-1.5b Q4_K_M on llama-server",
        "",
        f"{report.get('timestamp', '')} · llama.cpp {run.get('llama_build') or '?'} · "
        f"{run.get('cpu_model') or '?'} ({run.get('cpu_cores') or '?'} cores, {run.get('ram_gb') or '?'} GB RAM)",
        "",
        "| Prompt | TTFT (s) | Tokens | tok/s (server) | tok/s (wall) | Prompt eval tok/s | Finish |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for r in report.get("results", []):
        if r.get("error"):
            out.append(f"| `{r['id']}` | – | – | – | – | – | error: {r['error'][:80]} |")
            continue
        out.append(
            f"| `{r['id']}` | {_fmt(r['ttft_s'])} | {_fmt(r['completion_tokens'])} | {_fmt(r['gen_tok_s'])} | "
            f"{_fmt(r['wall_tok_s'])} | {_fmt(r['prompt_tok_s'])} | {_fmt(r['finish_reason'])} |"
        )
    out += [
        "",
        f"All prompts: {_fmt(agg.get('completion_tokens'))} tokens, {_fmt(agg.get('gen_tok_s'))} tok/s (server), "
        f"{_fmt(agg.get('overall_tok_s'))} tok/s incl. prompt eval, mean TTFT {_fmt(agg.get('mean_ttft_s'), ' s')}.",
    ]
    if ref:
        gr = next((r for r in report.get("results", []) if r.get("id") == ref.get("prompt_id")), None)
        here = gr.get("gen_tok_s") if gr and not gr.get("error") else None
        ratio = f" ({here / ref['tok_s']:.2f}× the box)" if here and ref.get("tok_s") else ""
        out.append(
            f"Reference `{ref.get('prompt_id')}` on {ref.get('where')}: {ref.get('completion_tokens')} tokens in "
            f"{ref.get('seconds')} s = **{ref.get('tok_s')} tok/s**; this run: **{_fmt(here)} tok/s**{ratio}."
        )
    out.append(f"Model sha256 `{run.get('model_sha256') or '?'}` · seed {report.get('params', {}).get('seed')} · "
               f"temperature {report.get('params', {}).get('temperature')}")
    return "\n".join(out) + "\n"


# --------------------------------------------------------------------------- runner info

def now_iso_new_york() -> str:
    try:
        from zoneinfo import ZoneInfo

        tz = ZoneInfo("America/New_York")
    except Exception:  # no tzdata: fall back to EDT
        tz = timezone(timedelta(hours=-4), "EDT")
    return datetime.now(tz).isoformat(timespec="seconds")


def runner_info(model_sha256: str | None = None, llama_build: str | None = None) -> dict:
    cpu_model = None
    try:
        for line in Path("/proc/cpuinfo").read_text(encoding="utf-8", errors="replace").splitlines():
            if line.lower().startswith("model name"):
                cpu_model = line.split(":", 1)[1].strip()
                break
    except OSError:
        pass
    ram_gb = None
    try:
        for line in Path("/proc/meminfo").read_text().splitlines():
            if line.startswith("MemTotal:"):
                ram_gb = round(int(line.split()[1]) / 1024 / 1024, 1)
                break
    except (OSError, ValueError, IndexError):
        pass
    return {
        "cpu_model": cpu_model or platform.processor() or None,
        "cpu_cores": os.cpu_count(),
        "ram_gb": ram_gb,
        "os": platform.platform(),
        "python": platform.python_version(),
        "runner_name": os.environ.get("RUNNER_NAME"),
        "runner_os": os.environ.get("RUNNER_OS"),
        "github_run_id": os.environ.get("GITHUB_RUN_ID"),
        "github_sha": os.environ.get("GITHUB_SHA"),
        "llama_build": llama_build,
        "model_sha256": model_sha256,
    }


# --------------------------------------------------------------------------- HTTP

def _get_json(url: str, timeout: float = 10) -> dict:
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def server_build(base_url: str) -> str | None:
    try:
        props = _get_json(base_url.rstrip("/") + "/props")
    except (OSError, ValueError, urllib.error.URLError):
        return None
    return props.get("build_info") or None


def run_prompt(base_url: str, model: str, prompt: str, seed: int, max_tokens: int, timeout: float) -> dict:
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": True,
        "stream_options": {"include_usage": True},
        "temperature": 0,
        "seed": seed,
        "max_tokens": max_tokens,
        "cache_prompt": False,
    }
    req = urllib.request.Request(
        base_url.rstrip("/") + "/v1/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", "Accept": "text/event-stream"},
        method="POST",
    )
    t0 = time.monotonic()
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return parse_stream(resp, clock=time.monotonic, t_start=t0)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--url", default=os.environ.get("BENCH_URL", DEFAULT_URL))
    ap.add_argument("--model", default=os.environ.get("BENCH_MODEL", DEFAULT_MODEL))
    ap.add_argument("--seed", type=int, default=DEFAULT_SEED)
    ap.add_argument("--max-tokens", type=int, default=int(os.environ.get("BENCH_MAX_TOKENS", DEFAULT_MAX_TOKENS)))
    ap.add_argument("--timeout", type=float, default=600.0, help="per-request socket timeout (s)")
    ap.add_argument("--only", action="append", help="run only these prompt ids (repeatable)")
    ap.add_argument("--no-warmup", action="store_true")
    ap.add_argument("--model-sha256", default=os.environ.get("MODEL_SHA256"))
    ap.add_argument("--llama-build", default=os.environ.get("LLAMA_TAG"))
    ap.add_argument("--out", default="bench.json")
    args = ap.parse_args(argv)

    prompts = [p for p in PROMPTS if not args.only or p["id"] in args.only]
    if not prompts:
        ap.error(f"no prompts match {args.only}; known: {[p['id'] for p in PROMPTS]}")

    build = server_build(args.url)
    llama_build = args.llama_build
    if build and llama_build and build not in llama_build:
        llama_build = f"{llama_build} ({build})"
    elif build and not llama_build:
        llama_build = build

    if not args.no_warmup:  # load weights into the page cache; not recorded
        try:
            run_prompt(args.url, args.model, "Hi", args.seed, 8, args.timeout)
        except Exception as e:  # noqa: BLE001
            print(f"warmup failed: {e}", file=sys.stderr)

    results = []
    for p in prompts:
        try:
            parsed = run_prompt(args.url, args.model, p["prompt"], args.seed, args.max_tokens, args.timeout)
            rec = summarize(p["id"], parsed)
            if parsed.get("system_fingerprint") and not llama_build:
                llama_build = parsed["system_fingerprint"]
        except Exception as e:  # noqa: BLE001
            rec = {"id": p["id"], "error": f"{type(e).__name__}: {e}"}
        rec["prompt"] = p["prompt"]
        results.append(rec)
        print(json.dumps(rec, ensure_ascii=False), flush=True)

    report = {
        "schema": SCHEMA,
        "timestamp": now_iso_new_york(),
        "server_url": args.url,
        "model": args.model,
        "params": {"seed": args.seed, "temperature": 0, "max_tokens": args.max_tokens, "stream": True},
        "runner": runner_info(args.model_sha256, llama_build),
        "results": results,
        "aggregate": aggregate(results),
        "reference": REFERENCE,
    }
    Path(args.out).write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    md = markdown_table(report)
    print(md)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as f:
            f.write(md)
    return 0 if report["aggregate"]["prompts_ok"] == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
