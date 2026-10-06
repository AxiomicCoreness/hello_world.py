#!/usr/bin/env python3
"""
workload_dispatch — terminal relay channel for text-to-speech chat.

Reads lines from stdin, speaks them via a local TTS backend, and
optionally forwards them to an MCP endpoint. Replies from the MCP
gate (if reachable) are printed and spoken back.

    python3 workload_dispatch.py                 # interactive chat loop
    python3 workload_dispatch.py --say "hi"      # one-shot speak
    python3 workload_dispatch.py --relay URL     # relay to MCP gate

TTS backends tried in order:
    macOS   : `say`  (built in)
    Linux   : `espeak-ng` or `espeak`, else `spd-say`, else `festival`
    fallback: print-only (still works, no audio)

Env:
    MCP_URL       optional, e.g. http://127.0.0.1:8024
    MCP_SECRET    optional, sent as X-Garden-Secret
    TTS_VOICE     optional, backend-specific voice name

Name note: this file is not quantum/batch_simd_tuning.py::workload_dispatch
(EM-006 JSON packaging). Separate surface.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.request


def find_tts() -> list[str] | None:
    """Return argv prefix for the first available TTS backend, or None."""
    voice = os.environ.get("TTS_VOICE")
    if shutil.which("say"):  # macOS
        return ["say"] + (["-v", voice] if voice else [])
    if shutil.which("espeak-ng"):
        return ["espeak-ng"] + (["-v", voice] if voice else [])
    if shutil.which("espeak"):
        return ["espeak"] + (["-v", voice] if voice else [])
    if shutil.which("spd-say"):
        return ["spd-say"] + (["-y", voice] if voice else [])
    if shutil.which("festival"):
        return ["festival", "--tts"]
    return None


def speak(prefix: list[str] | None, text: str) -> None:
    """Speak text, or print it with a marker if no TTS is available."""
    if not text.strip():
        return
    if prefix is None:
        print(f"[tts-unavailable] {text}", file=sys.stderr)
        return
    try:
        subprocess.run(
            prefix + [text],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception as e:
        print(f"[tts-error] {e}", file=sys.stderr)


def relay(url: str, secret: str | None, payload: dict, timeout: float = 10.0) -> dict:
    """POST payload to the MCP gate, return parsed JSON or an error dict."""
    data = json.dumps(payload).encode()
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if secret:
        headers["X-Garden-Secret"] = secret
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read().decode("utf-8", "replace")
            try:
                return json.loads(body)
            except json.JSONDecodeError:
                return {"status": r.status, "raw": body[:400]}
    except urllib.error.HTTPError as e:
        return {"status": e.code, "error": e.read().decode("utf-8", "replace")[:400]}
    except (urllib.error.URLError, TimeoutError) as e:
        return {"status": None, "error": str(e)}


def chat_loop(tts: list[str] | None, mcp_url: str | None, mcp_secret: str | None) -> int:
    banner = "workload_dispatch — type text, blank line or Ctrl-D to exit"
    print(banner, file=sys.stderr)
    while True:
        try:
            line = input("> ")
        except EOFError:
            print(file=sys.stderr)
            break
        if not line.strip():
            break
        speak(tts, line)
        if mcp_url:
            endpoint = mcp_url.rstrip("/") + "/mcp/tool"
            reply = relay(endpoint, mcp_secret, {"tool": "chat", "text": line})
            print(f"<- {json.dumps(reply)}", file=sys.stderr)
            for key in ("text", "reply", "message"):
                if isinstance(reply, dict) and isinstance(reply.get(key), str):
                    speak(tts, reply[key])
                    break
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="workload_dispatch")
    p.add_argument("--say", metavar="TEXT", help="speak TEXT once and exit")
    p.add_argument(
        "--relay",
        metavar="URL",
        help="MCP gate URL (overrides MCP_URL env)",
    )
    p.add_argument(
        "--list-backend",
        action="store_true",
        help="show which TTS backend would be used",
    )
    args = p.parse_args(argv)

    tts = find_tts()
    mcp_url = args.relay or os.environ.get("MCP_URL")
    mcp_secret = os.environ.get("MCP_SECRET")

    if args.list_backend:
        print(tts[0] if tts else "(none — print-only fallback)")
        return 0
    if args.say is not None:
        speak(tts, args.say)
        return 0
    return chat_loop(tts, mcp_url, mcp_secret)


if __name__ == "__main__":
    raise SystemExit(main())
