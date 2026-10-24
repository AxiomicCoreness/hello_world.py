"""Tiny loopback-only OpenAI-style chat client shared by the forlorn evals."""
from __future__ import annotations

import argparse
import json
import os
import urllib.request
from urllib.parse import urlsplit

DEFAULT_URL = os.environ.get("CYT_EVAL_URL", "http://127.0.0.1:8082/v1/chat/completions")
LOOPBACK = {"127.0.0.1", "localhost", "::1"}


def parse_args(doc: str) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=doc.splitlines()[0])
    ap.add_argument("--url", default=DEFAULT_URL, help="loopback /v1/chat/completions URL")
    ap.add_argument("--json", action="store_true", help="print one JSON result line")
    a = ap.parse_args()
    host = urlsplit(a.url).hostname
    if host not in LOOPBACK:
        raise SystemExit(f"FATAL: Cosmic Alignment — eval URL must be loopback, got {host!r}")
    return a


def chat(url: str, prompt: str, *, system: str | None = None, max_tokens: int = 192) -> str:
    msgs = ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": prompt}]
    body = {"messages": msgs, "max_tokens": max_tokens, "temperature": 0, "seed": 0}
    req = urllib.request.Request(url, json.dumps(body).encode(), {"Content-Type": "application/json"})
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(req, timeout=180) as resp:
        return json.load(resp)["choices"][0]["message"]["content"]


def report(name: str, cases: list, as_json: bool) -> int:
    passed = sum(1 for c in cases if c["pass"])
    for c in cases:
        print(f"[{'PASS' if c['pass'] else 'FAIL'}] {name}: {c['id']}: {c['why']}")
        print(f"       reply: {c['reply']!r}")
    print(f"{name}: {passed}/{len(cases)} passed")
    if as_json:
        print(json.dumps({"eval": name, "passed": passed, "total": len(cases)}))
    return 0 if passed == len(cases) else 1
