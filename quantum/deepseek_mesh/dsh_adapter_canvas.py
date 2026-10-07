#!/usr/bin/env python3
"""
quantum/deepseek_mesh/dsh_adapter.py — Clarke Yoursa Tee

Thin adapter between the REPL / workload_dispatch and one of:
  - a DeepSeek-compatible HTTP endpoint        (--prefer deepseek_http)
  - a client_secret-backed HTTP endpoint       (--prefer client_secret_http)
  - the in-tree sovereign automaton, loaded    (--prefer sovereign)
    from garden_surgery/sovereign_automaton_10.06.py by file path

Contract:
  stdin/stdout only. --prompt STR → prints one JSON object on stdout:
    {"text": "...", "model": "...", "latency_ms": N, "meta": {"usage": {...}}}
  Nonzero exit on failure; stderr carries the reason.

Environment (read lazily, only by the selected backend):
  DEEPSEEK_API_KEY        for deepseek_http
  DEEPSEEK_BASE_URL       default https://api.deepseek.com
  DEEPSEEK_MODEL          default "deepseek-chat"
  CLIENT_SECRET           for client_secret_http
  CLIENT_SECRET_BASE_URL  required for client_secret_http (no default)
  SOVEREIGN_AUTOMATON     override path to the automaton file
                          default: garden_surgery/sovereign_automaton_10.06.py

--dry-run: resolve the selected backend, report what it would do, exit 0.
           This is the mode that works before any credential is set and
           before the automaton's callable surface has been confirmed.

The adapter does NOT hardcode an automaton function name. It searches the
module for a plausible entrypoint (chat / respond / run / generate / ask
/ __call__ on a class named *Automaton*), and if none match, exits with
the exact grep command to run:

    grep -n "def \\|class " garden_surgery/sovereign_automaton_10.06.py | head -40

Resolving the entrypoint is the one prerequisite for the sovereign
backend to actually run. This file is written so that its --help and
--dry-run work today and its real call works the moment the surface is
named.
"""

from __future__ import annotations

import argparse
import importlib.util
import inspect
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

VERSION = "1.0"

DEFAULT_AUTOMATON_PATH = "garden_surgery/sovereign_automaton_10.06.py"

_ENTRYPOINT_NAMES = (
    "chat", "respond", "reply", "run", "generate", "ask",
    "answer", "invoke", "handle", "process",
)


class AdapterError(RuntimeError):
    pass


def _http_chat(base_url: str, api_key: str, model: str, prompt: str) -> dict:
    url = base_url.rstrip("/") + "/chat/completions"
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            body = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise AdapterError(
            f"{base_url} HTTP {e.code}: "
            f"{e.read().decode('utf-8', errors='replace')[:400]}"
        )
    except (urllib.error.URLError, TimeoutError) as e:
        raise AdapterError(f"{base_url} transport: {e}")
    latency = int((time.time() - t0) * 1000)

    try:
        text = body["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        raise AdapterError(
            f"{base_url} returned unrecognized shape: "
            f"{json.dumps(body)[:400]}"
        )

    return {
        "text": text,
        "model": body.get("model", model),
        "latency_ms": latency,
        "meta": {"usage": body.get("usage", {})},
    }


def _backend_deepseek_http(prompt: str, dry_run: bool) -> dict:
    key = os.environ.get("DEEPSEEK_API_KEY")
    base = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    model = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")
    if dry_run:
        return {"_dry_run": True, "backend": "deepseek_http",
                "base_url": base, "model": model,
                "api_key": "set" if key else "UNSET"}
    if not key:
        raise AdapterError("deepseek_http requires DEEPSEEK_API_KEY")
    return _http_chat(base, key, model, prompt)


def _backend_client_secret_http(prompt: str, dry_run: bool) -> dict:
    secret = os.environ.get("CLIENT_SECRET")
    base = os.environ.get("CLIENT_SECRET_BASE_URL")
    model = os.environ.get("CLIENT_SECRET_MODEL", "default")
    if dry_run:
        return {"_dry_run": True, "backend": "client_secret_http",
                "base_url": base or "UNSET (CLIENT_SECRET_BASE_URL required)",
                "model": model,
                "client_secret": "set" if secret else "UNSET"}
    if not secret:
        raise AdapterError("client_secret_http requires CLIENT_SECRET")
    if not base:
        raise AdapterError(
            "client_secret_http requires CLIENT_SECRET_BASE_URL "
            "(no default — the endpoint must be named explicitly)"
        )
    return _http_chat(base, secret, model, prompt)


def _load_automaton(path: Path):
    if not path.is_file():
        raise AdapterError(f"automaton not found: {path}")
    spec = importlib.util.spec_from_file_location(
        "sovereign_automaton_dynamic", str(path)
    )
    if spec is None or spec.loader is None:
        raise AdapterError(f"cannot build import spec for {path}")
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception as e:
        raise AdapterError(
            f"automaton failed to import: {type(e).__name__}: {e}"
        )
    return mod


def _resolve_entrypoint(mod) -> tuple[object, str]:
    """Return (callable, qualified_name). Search, do not guess."""
    for name in _ENTRYPOINT_NAMES:
        fn = getattr(mod, name, None)
        if callable(fn):
            return fn, f"{mod.__name__}.{name}"
    for cname in dir(mod):
        if "Automaton" not in cname:
            continue
        cls = getattr(mod, cname)
        if not inspect.isclass(cls):
            continue
        for name in _ENTRYPOINT_NAMES:
            m = getattr(cls, name, None)
            if m is None or not callable(m):
                continue
            try:
                inst = cls()
            except Exception:
                continue
            bound = getattr(inst, name)
            return bound, f"{cname}().{name}"
    for cname in dir(mod):
        if "Automaton" not in cname:
            continue
        cls = getattr(mod, cname)
        if not inspect.isclass(cls):
            continue
        try:
            inst = cls()
        except Exception:
            continue
        if callable(inst):
            return inst, f"{cname}()()"
    raise AdapterError(
        "no entrypoint matched in the automaton module. "
        "Run and paste:\n"
        '  grep -n "def \\|class " '
        f"{DEFAULT_AUTOMATON_PATH} | head -40\n"
        "Then name the function that takes text and returns text; "
        "this adapter will use it."
    )


def _backend_sovereign(prompt: str, dry_run: bool) -> dict:
    path = Path(os.environ.get("SOVEREIGN_AUTOMATON", DEFAULT_AUTOMATON_PATH))
    if dry_run:
        found = path.is_file()
        return {"_dry_run": True, "backend": "sovereign",
                "path": str(path), "file_present": found,
                "note": ("resolve entrypoint would run here"
                         if found else
                         "automaton file not found at this path")}
    mod = _load_automaton(path)
    fn, qname = _resolve_entrypoint(mod)
    t0 = time.time()
    try:
        reply = fn(prompt)
    except TypeError as e:
        raise AdapterError(
            f"entrypoint {qname} rejected the call signature "
            f"fn(text). Actual signature: "
            f"{inspect.signature(fn) if callable(fn) else '?'} — {e}"
        )
    latency = int((time.time() - t0) * 1000)
    if isinstance(reply, bytes):
        reply = reply.decode("utf-8", errors="replace")
    if not isinstance(reply, str):
        reply = json.dumps(reply, ensure_ascii=False, default=str)
    return {
        "text": reply,
        "model": qname,
        "latency_ms": latency,
        "meta": {"usage": {}},
    }


_BACKENDS = {
    "deepseek_http":       _backend_deepseek_http,
    "client_secret_http":  _backend_client_secret_http,
    "sovereign":           _backend_sovereign,
}

DEFAULT_PREFER = "deepseek_http"


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="dsh_adapter",
        description="Thin chat adapter: HTTP (DeepSeek / client_secret) "
                    "or the in-tree sovereign automaton.",
    )
    p.add_argument("--prefer", choices=sorted(_BACKENDS),
                   default=DEFAULT_PREFER,
                   help="backend to use (default: %(default)s)")
    p.add_argument("--prompt", default=None,
                   help="prompt text; if omitted, read from stdin")
    p.add_argument("--dry-run", action="store_true",
                   help="resolve the backend and report, do not call")
    p.add_argument("--version", action="version",
                   version=f"dsh_adapter {VERSION}")
    return p.parse_args(argv)


def main(argv: list[str]) -> int:
    args = _parse_args(argv)

    if args.dry_run:
        try:
            info = _BACKENDS[args.prefer]("", dry_run=True)
        except AdapterError as e:
            print(json.dumps({"error": str(e)}, ensure_ascii=False))
            return 1
        print(json.dumps(info, ensure_ascii=False, indent=2))
        return 0

    prompt = args.prompt
    if prompt is None:
        prompt = sys.stdin.read()
    if not prompt:
        print(json.dumps({"error": "empty prompt"}), file=sys.stderr)
        return 2

    try:
        result = _BACKENDS[args.prefer](prompt, dry_run=False)
    except AdapterError as e:
        print(json.dumps({"error": str(e)}, ensure_ascii=False),
              file=sys.stderr)
        return 1
    except Exception as e:
        print(json.dumps(
            {"error": f"{type(e).__name__}: {e}"}, ensure_ascii=False),
            file=sys.stderr)
        return 1

    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
