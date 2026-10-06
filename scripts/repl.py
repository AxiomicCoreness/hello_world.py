#!/usr/bin/env python3
"""repl.py — persistent chat REPL over quantum.deepseek_mesh.dsh_adapter.

History is stored as JSONL under ~/.deepseek_repl/sessions/.
Each session is a file named <timestamp>-<ns>-<pid>-<slug>.jsonl.

Commands:
    +new [name]      start a new session (optionally named)
    +list            list saved sessions (most recent first)
    +load <id>       load a session by id or id-prefix
    +del <id>        delete a session by id or id-prefix
    +backend <name>  switch backend for the current session
    +backends        list available backends and whether their env var is set
    +h               show current session history
    +c               clear current session (in memory only; file untouched)
    +q               quit

Adapter shape (from observed output):
    {
      "mode": "deepseek_http",
      "text": "...",
      "model": "deepseek-chat",
      "latency_ms": 633.5,
      "meta": { "usage": { "prompt_tokens": 6, "completion_tokens": 9,
                           "total_tokens": 15 } }
    }

No credential is written to disk. Session files contain only chat turns.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

STORE = Path.home() / ".deepseek_repl" / "sessions"
STORE.mkdir(parents=True, exist_ok=True)

USER_TAG = ">>> "
ASSIST_TAG = "<<< "


ALL_CREDENTIAL_VARS = {"DEEPSEEK_API_KEY", "CLIENT_SECRET"}

BACKENDS = {
    "deepseek": {
        "prefer": "deepseek_http",
        "env_var": "DEEPSEEK_API_KEY",
    },
    "client_secret": {
        "prefer": "client_secret_http",
        "env_var": "CLIENT_SECRET",
    },
}

DEFAULT_BACKEND = "deepseek"


def backend_env_ok(name: str) -> bool:
    spec = BACKENDS.get(name)
    if not spec:
        return False
    var = spec.get("env_var")
    return bool(var and os.environ.get(var))


def backend_prefer(name: str) -> str | None:
    spec = BACKENDS.get(name)
    return spec.get("prefer") if spec else None


def list_backends() -> None:
    print(f"default: {DEFAULT_BACKEND}")
    for name, spec in BACKENDS.items():
        var = spec.get("env_var", "?")
        prefer = spec.get("prefer", "?")
        mark = "set" if os.environ.get(var) else "unset"
        print(f"  {name:16s} prefer={prefer:24s} env={var} [{mark}]")


def new_session(name: str | None = None, backend: str = DEFAULT_BACKEND) -> dict:
    ts = time.strftime("%Y%m%d-%H%M%S")
    ns = time.time_ns() % 1_000_000_000
    pid = os.getpid()
    slug = (name or "chat").replace(" ", "_").replace("/", "_")[:32]
    path = STORE / f"{ts}-{ns:09d}-{pid}-{slug}.jsonl"
    path.touch()
    return {"path": path, "history": [], "backend": backend}


def load_session(prefix: str) -> dict | None:
    matches = [p for p in STORE.iterdir() if p.stem.startswith(prefix)]
    if not matches:
        print(f"[no session matching {prefix!r}]")
        return None
    path = sorted(matches)[-1]
    history: list[dict] = []
    backend = DEFAULT_BACKEND
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(rec, dict) and rec.get("_meta") == "backend":
                backend = rec.get("value", DEFAULT_BACKEND)
                continue
            history.append(rec)
    return {"path": path, "history": history, "backend": backend}


def append(session: dict, msg: dict) -> None:
    session["history"].append(msg)
    with open(session["path"], "a", encoding="utf-8") as f:
        f.write(json.dumps(msg, ensure_ascii=False) + "\n")


def append_backend(session: dict, backend: str) -> None:
    session["backend"] = backend
    with open(session["path"], "a", encoding="utf-8") as f:
        f.write(json.dumps({"_meta": "backend", "value": backend}, ensure_ascii=False) + "\n")


def list_sessions(limit: int = 20) -> None:
    rows = []
    for p in sorted(STORE.iterdir(), reverse=True):
        try:
            size = p.stat().st_size
            with open(p, "r", encoding="utf-8") as f:
                n = sum(1 for _ in f)
        except OSError:
            continue
        rows.append((p.stem, n, size))
    if not rows:
        print("[no sessions]")
        return
    for stem, n, size in rows[:limit]:
        print(f"  {stem:56s} {n:4d} lines  {size:8d} b")


def flatten(history: list[dict]) -> str:
    parts = []
    for m in history:
        if m.get("role") == "user":
            parts.append(f"{USER_TAG}{m.get('content', '')}")
        else:
            parts.append(f"{ASSIST_TAG}{m.get('content', '')}")
    return "\n".join(parts)


def call_adapter(history: list[dict], backend: str) -> tuple[dict | None, str | None]:
    prefer = backend_prefer(backend)
    if not prefer:
        return None, f"unknown backend: {backend!r}"
    spec = BACKENDS[backend]
    var = spec.get("env_var")
    if var and not os.environ.get(var):
        return None, f"backend {backend!r} requires env var {var}, which is unset"
    env = dict(os.environ)
    for other in ALL_CREDENTIAL_VARS - {var}:
        env.pop(other, None)
    prompt = flatten(history)
    cmd = [sys.executable, "-m", "quantum.deepseek_mesh.dsh_adapter", "--prefer", prefer, "--prompt", prompt]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=180, env=env)
    except subprocess.TimeoutExpired:
        return None, "adapter timed out after 180s"
    except FileNotFoundError as e:
        return None, f"adapter not found: {e}"
    if r.returncode != 0:
        return None, r.stderr.strip() or r.stdout.strip() or f"exit {r.returncode}"
    try:
        out = json.loads(r.stdout)
    except json.JSONDecodeError as e:
        return None, f"json decode: {e}; stdout[:200]={r.stdout[:200]!r}"
    out["_usage"] = out.get("meta", {}).get("usage", {})
    out["_backend"] = backend
    return out, None


HELP = """commands:
    +new [name]      start a new session
    +list            list saved sessions
    +load <id>       load a session by id-prefix
    +del <id>        delete a session by id-prefix
    +backend <name>  switch backend for the current session
    +backends        list available backends and env-var status
    +h               show current session history
    +c               clear current session (memory only)
    +q               quit
"""


def main() -> int:
    session = new_session()
    print(f"session: {session['path'].stem}")
    print(f"backend: {session['backend']}")
    print(HELP.rstrip())
    while True:
        try:
            line = input(">>> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not line:
            continue
        if line == "+q":
            break
        if line == "+h":
            if not session["history"]:
                print("[empty]")
                continue
            for i, m in enumerate(session["history"]):
                tag = "U" if m.get("role") == "user" else "A"
                preview = str(m.get("content", "")).replace("\n", " ")[:100]
                print(f"  {i:3d} {tag}  {preview}")
            continue
        if line == "+c":
            session["history"].clear()
            print("[cleared in memory; file untouched]")
            continue
        if line == "+backends":
            list_backends()
            continue
        if line.startswith("+backend"):
            name = line[8:].strip()
            if not name:
                print(f"[current: {session['backend']}]")
                continue
            if name not in BACKENDS:
                print(f"[unknown backend: {name!r}]")
                list_backends()
                continue
            session["backend"] = name
            append_backend(session, name)
            warn = "" if backend_env_ok(name) else " (env var unset)"
            print(f"[backend: {name}{warn}]")
            continue
        if line.startswith("+new"):
            name = line[4:].strip() or None
            session = new_session(name, backend=session["backend"])
            print(f"[new session: {session['path'].stem}]")
            print(f"[backend: {session['backend']}]")
            continue
        if line == "+list":
            list_sessions()
            continue
        if line.startswith("+load"):
            prefix = line[5:].strip()
            if not prefix:
                print("[usage: +load <id-prefix>]")
                continue
            loaded = load_session(prefix)
            if loaded:
                session = loaded
                print(f"[loaded {session['path'].stem}, {len(session['history'])} msgs, backend={session['backend']}]")
            continue
        if line.startswith("+del"):
            prefix = line[4:].strip()
            if not prefix:
                print("[usage: +del <id-prefix>]")
                continue
            matches = [p for p in STORE.iterdir() if p.stem.startswith(prefix)]
            for p in matches:
                try:
                    p.unlink()
                except OSError as e:
                    print(f"[unlink {p.name}: {e}]")
            print(f"[deleted {len(matches)}]")
            continue
        user_msg = {"role": "user", "content": line}
        append(session, user_msg)
        out, err = call_adapter(session["history"], session["backend"])
        if err:
            print(f"[adapter error] {err}", file=sys.stderr)
            continue
        reply = out.get("text", "") or ""
        usage = out.get("_usage", {})
        latency = out.get("latency_ms", "?")
        model = out.get("model", "?")
        backend = out.get("_backend", "backend")
        print(reply)
        total = usage.get("total_tokens", "?")
        print(f"  [{backend} · {model} · {total} tok · {latency} ms]")
        append(session, {"role": "assistant", "content": reply})
    print(f"[session closed: {session['path'].stem}]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
