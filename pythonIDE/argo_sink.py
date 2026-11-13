# SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
# SPDX-License-Identifier: MIT
"""Backend Argo CI/CD sink (Section IV, filled).

Polls the GitHub Actions runs of the Argo / CI/CD workflows on ``main`` and
pushes one status line per workflow to the loopback CLI bridge
``ws://127.0.0.1:6680/cli`` as a WebSocket client. This replaces a browser tab
as the bridge client for CI status.

Bind policy: the HTTP side listens on ``127.0.0.1:8024`` only. The bridge URL
must also be loopback. A token, when present (``GITHUB_TOKEN`` / ``GH_TOKEN``),
is sent only as an Authorization header to api.github.com and never logged.

Stdlib only (urllib, socket, http.server). NO_LEDGER_WRITE from this module.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import socket
import ssl
import struct
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Callable, Dict, List, Optional, Tuple

BIND_HOST = "127.0.0.1"
BIND_PORT = 8024
BIND = f"{BIND_HOST}:{BIND_PORT}"
FILLED = True
LEDGER_GENESIS = 9195
REPO = "AxiomicCoreness/hello_world.py"
BRANCH = "main"
CLI_URL = "ws://127.0.0.1:6680/cli"
API_ROOT = "https://api.github.com"
WORKFLOWS: Tuple[str, ...] = (
    "argo-ci.yml",
    "cd-combinator-argo-rollout.yml",
    "sovereign-cicd.yml",
    "ci-cd-stack.yml",
)
LOOPBACK_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})
HTTP_TIMEOUT_S = 8.0
WS_TIMEOUT_S = 5.0

Fetcher = Callable[[str, Optional[str]], Dict[str, Any]]

_STATE: Dict[str, Any] = {"last_poll": None, "lines": [], "results": []}
_STATE_LOCK = threading.Lock()


class SinkError(Exception):
    """Sink-level failure (bind policy, WS handshake, HTTP)."""


def assert_loopback_host(host: str) -> str:
    h = (host or "").strip().strip("[]")
    if h not in LOOPBACK_HOSTS:
        raise SinkError(f"refusing non-loopback bind/target: {host!r}")
    return h


def _token() -> Optional[str]:
    tok = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or ""
    tok = tok.strip()
    return tok or None


def http_get_json(url: str, token: Optional[str] = None) -> Dict[str, Any]:
    """GET a GitHub API URL and decode JSON. Token goes only in the header."""
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    req.add_header("User-Agent", "argo-sink/1.0")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT_S) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise SinkError(f"HTTP {exc.code} for {url}") from None
    except (urllib.error.URLError, OSError, ValueError) as exc:
        raise SinkError(f"{type(exc).__name__}: {exc}") from None


def runs_url(workflow: str, repo: str = REPO, branch: str = BRANCH, per_page: int = 1) -> str:
    q = urllib.parse.urlencode({"branch": branch, "per_page": per_page})
    return f"{API_ROOT}/repos/{repo}/actions/workflows/{urllib.parse.quote(workflow)}/runs?{q}"


def latest_run(workflow: str, fetch: Optional[Fetcher] = None, token: Optional[str] = None) -> Dict[str, Any]:
    fetch = fetch or http_get_json
    data = fetch(runs_url(workflow), token)
    runs = data.get("workflow_runs") or []
    if not runs:
        return {"workflow": workflow, "found": False}
    r = runs[0]
    return {
        "workflow": workflow,
        "found": True,
        "name": r.get("name"),
        "run_id": r.get("id"),
        "run_number": r.get("run_number"),
        "event": r.get("event"),
        "status": r.get("status"),
        "conclusion": r.get("conclusion"),
        "branch": r.get("head_branch"),
        "sha": (r.get("head_sha") or "")[:8],
        "created_at": r.get("created_at"),
        "url": r.get("html_url"),
    }


def status_line(res: Dict[str, Any]) -> str:
    wf = res.get("workflow")
    if res.get("error"):
        return f"[Argo] {wf} · error · {res['error']}"
    if not res.get("found"):
        return f"[Argo] {wf} · no runs on {BRANCH}"
    state = res.get("conclusion") or res.get("status") or "unknown"
    return (
        f"[Argo] {wf} · {res.get('name')} · run {res.get('run_number')} · {state}"
        f" · {res.get('branch')}@{res.get('sha')} · {res.get('event')} · {res.get('created_at')}"
    )


def poll_once(
    workflows: Tuple[str, ...] = WORKFLOWS,
    fetch: Optional[Fetcher] = None,
    token: Optional[str] = None,
) -> List[Dict[str, Any]]:
    token = token if token is not None else _token()
    out: List[Dict[str, Any]] = []
    for wf in workflows:
        try:
            out.append(latest_run(wf, fetch=fetch, token=token))
        except Exception as exc:  # noqa: BLE001 — one bad workflow must not stop the poll
            out.append({"workflow": wf, "found": False, "error": str(exc)})
    with _STATE_LOCK:
        _STATE["last_poll"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        _STATE["results"] = out
        _STATE["lines"] = [status_line(r) for r in out]
    return out


class WSClient:
    """Minimal RFC 6455 text-frame client for the loopback CLI bridge."""

    def __init__(self, url: str = CLI_URL, timeout: float = WS_TIMEOUT_S) -> None:
        u = urllib.parse.urlsplit(url)
        if u.scheme not in {"ws", "wss"}:
            raise SinkError(f"bridge URL must be ws:// or wss://, got {url!r}")
        self.host = assert_loopback_host(u.hostname or "")
        self.port = u.port or (443 if u.scheme == "wss" else 80)
        self.path = (u.path or "/") + (f"?{u.query}" if u.query else "")
        self.secure = u.scheme == "wss"
        self.timeout = timeout
        self.sock: Optional[socket.socket] = None
        self._buf = b""

    def connect(self) -> "WSClient":
        raw = socket.create_connection((self.host, self.port), timeout=self.timeout)
        if self.secure:
            raw = ssl.create_default_context().wrap_socket(raw, server_hostname=self.host)
        key = base64.b64encode(os.urandom(16)).decode("ascii")
        req = (
            f"GET {self.path} HTTP/1.1\r\n"
            f"Host: {self.host}:{self.port}\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\n"
            "Sec-WebSocket-Version: 13\r\n"
            "User-Agent: argo-sink/1.0\r\n\r\n"
        )
        raw.sendall(req.encode("ascii"))
        head = b""
        while b"\r\n\r\n" not in head:
            chunk = raw.recv(4096)
            if not chunk:
                raise SinkError("bridge closed during handshake")
            head += chunk
        hdr, _, rest = head.partition(b"\r\n\r\n")
        status = hdr.split(b"\r\n", 1)[0].decode("latin-1")
        if " 101 " not in f"{status} ":
            raise SinkError(f"bridge handshake refused: {status}")
        self.sock = raw
        self._buf = rest
        return self

    def _recv_exact(self, n: int) -> bytes:
        assert self.sock is not None
        while len(self._buf) < n:
            chunk = self.sock.recv(65536)
            if not chunk:
                raise SinkError("bridge closed")
            self._buf += chunk
        out, self._buf = self._buf[:n], self._buf[n:]
        return out

    def _send_frame(self, opcode: int, payload: bytes) -> None:
        assert self.sock is not None
        mask = os.urandom(4)
        n = len(payload)
        head = bytes([0x80 | opcode])
        if n < 126:
            head += bytes([0x80 | n])
        elif n < 65536:
            head += bytes([0x80 | 126]) + struct.pack("!H", n)
        else:
            head += bytes([0x80 | 127]) + struct.pack("!Q", n)
        masked = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
        self.sock.sendall(head + mask + masked)

    def send_text(self, text: str) -> None:
        self._send_frame(0x1, text.encode("utf-8"))

    def recv_text(self, timeout: Optional[float] = None) -> Optional[str]:
        assert self.sock is not None
        self.sock.settimeout(timeout if timeout is not None else self.timeout)
        parts: List[bytes] = []
        while True:
            b1, b2 = self._recv_exact(2)
            fin, opcode = b1 & 0x80, b1 & 0x0F
            n = b2 & 0x7F
            if n == 126:
                n = struct.unpack("!H", self._recv_exact(2))[0]
            elif n == 127:
                n = struct.unpack("!Q", self._recv_exact(8))[0]
            mask = self._recv_exact(4) if b2 & 0x80 else b""
            data = self._recv_exact(n)
            if mask:
                data = bytes(b ^ mask[i % 4] for i, b in enumerate(data))
            if opcode == 0x8:
                return None
            if opcode == 0x9:
                self._send_frame(0xA, data)
                continue
            if opcode in (0x1, 0x2, 0x0):
                parts.append(data)
                if fin:
                    return b"".join(parts).decode("utf-8", errors="replace")

    def drain(self, quiet_s: float = 0.6) -> List[str]:
        got: List[str] = []
        while True:
            try:
                msg = self.recv_text(timeout=quiet_s)
            except (socket.timeout, TimeoutError):
                break
            if msg is None:
                break
            got.append(msg)
        return got

    def close(self) -> None:
        if self.sock is None:
            return
        try:
            self._send_frame(0x8, struct.pack("!H", 1000))
        except OSError:
            pass
        try:
            self.sock.close()
        finally:
            self.sock = None


def push_lines(lines: List[str], url: str = CLI_URL, probe: bool = True) -> Dict[str, Any]:
    """Connect to the bridge, push each line, collect the bridge replies."""
    ws = WSClient(url).connect()
    try:
        banner = ws.drain()
        replies: List[Dict[str, Any]] = []
        for line in lines:
            ws.send_text(line)
            replies.append({"sent": line, "replies": ws.drain()})
        if probe:
            ws.send_text("/py call argo")
            replies.append({"sent": "/py call argo", "replies": ws.drain(quiet_s=12.0)})
        return {"ok": True, "url": url, "banner": banner, "exchanges": replies}
    finally:
        ws.close()


def summary(fetch: Optional[Fetcher] = None) -> Dict[str, Any]:
    """Toolkit entry: poll only (never dials the bridge it may be running inside)."""
    results = poll_once(fetch=fetch)
    lines = [status_line(r) for r in results]
    ok = all(r.get("found") and not r.get("error") for r in results)
    return {
        "ok": ok,
        "repo": REPO,
        "branch": BRANCH,
        "workflows": list(WORKFLOWS),
        "lines": lines,
        "bind": BIND,
        "bridge": CLI_URL,
        "filled": FILLED,
    }


def handle_payload(payload: Dict[str, Any], fetch: Optional[Fetcher] = None) -> Dict[str, Any]:
    action = str((payload or {}).get("action") or "status").lower()
    if action == "status":
        with _STATE_LOCK:
            snap = dict(_STATE)
        return {"ok": True, "action": action, "bind": BIND, "mcp_filled": FILLED, **snap}
    if action == "poll":
        return {"ok": True, "action": action, **summary(fetch=fetch)}
    if action == "push":
        s = summary(fetch=fetch)
        try:
            pushed = push_lines(s["lines"], url=str(payload.get("url") or CLI_URL), probe=False)
        except (OSError, SinkError) as exc:
            return {"ok": False, "action": action, "error": f"{type(exc).__name__}: {exc}", **s}
        return {"ok": True, "action": action, **s, "push": pushed}
    return {"ok": False, "action": action, "reason": "unknown action (status|poll|push)"}


class _Handler(BaseHTTPRequestHandler):
    server_version = "argo-sink/1.0"

    def _send(self, code: int, body: Dict[str, Any]) -> None:
        raw = json.dumps(body, default=str).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            self._send(200, {"ok": True, "service": "argo-sink", "bind": BIND, "filled": FILLED})
        elif self.path == "/status":
            self._send(200, handle_payload({"action": "status"}))
        else:
            self._send(404, {"ok": False, "reason": "GET /health | /status, POST /payload"})

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/payload":
            self._send(404, {"ok": False})
            return
        n = int(self.headers.get("Content-Length") or 0)
        try:
            payload = json.loads(self.rfile.read(n).decode("utf-8") or "{}") if n else {}
        except ValueError:
            self._send(400, {"ok": False, "reason": "invalid JSON"})
            return
        self._send(200, handle_payload(payload))

    def log_message(self, fmt: str, *args: Any) -> None:
        sys.stderr.write("[argo-sink] " + (fmt % args) + "\n")


def make_server(host: str = BIND_HOST, port: int = BIND_PORT) -> ThreadingHTTPServer:
    return ThreadingHTTPServer((assert_loopback_host(host), int(port)), _Handler)


def _poll_loop(interval: float, url: str, push: bool, stop: threading.Event) -> None:
    while not stop.is_set():
        s = summary()
        for line in s["lines"]:
            print(line, flush=True)
        if push:
            try:
                res = push_lines(s["lines"], url=url, probe=False)
                print(f"[argo-sink] pushed {len(s['lines'])} line(s) to {url}", flush=True)
                for ex in res["exchanges"]:
                    for r in ex["replies"]:
                        print(f"[argo-sink] bridge: {r}", flush=True)
            except (OSError, SinkError) as exc:
                print(f"[argo-sink] bridge push failed: {type(exc).__name__}: {exc}", flush=True)
        stop.wait(interval)


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Backend Argo CI/CD sink → ws://127.0.0.1:6680/cli")
    ap.add_argument("--once", action="store_true", help="poll once, push, print bridge replies, exit")
    ap.add_argument("--serve", action="store_true", help="serve 127.0.0.1:8024 and poll on an interval")
    ap.add_argument("--interval", type=float, default=float(os.environ.get("ARGO_SINK_INTERVAL", "120")))
    ap.add_argument("--cli-url", default=os.environ.get("ARGO_SINK_CLI_URL", CLI_URL))
    ap.add_argument("--no-push", action="store_true", default=os.environ.get("ARGO_SINK_PUSH", "1") == "0")
    ap.add_argument("--port", type=int, default=int(os.environ.get("ARGO_SINK_PORT", str(BIND_PORT))))
    ns = ap.parse_args(argv)
    WSClient(ns.cli_url)
    if ns.serve:
        srv = make_server(BIND_HOST, ns.port)
        stop = threading.Event()
        t = threading.Thread(target=_poll_loop, args=(ns.interval, ns.cli_url, not ns.no_push, stop), daemon=True)
        t.start()
        print(f"[argo-sink] serving http://{BIND_HOST}:{ns.port} · bridge {ns.cli_url}", flush=True)
        try:
            srv.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            stop.set()
            srv.server_close()
        return 0
    s = summary()
    for line in s["lines"]:
        print(line)
    if ns.no_push:
        return 0 if s["ok"] else 1
    try:
        res = push_lines(s["lines"], url=ns.cli_url, probe=True)
    except (OSError, SinkError) as exc:
        print(f"[argo-sink] bridge push failed: {type(exc).__name__}: {exc}")
        return 2
    print(json.dumps(res, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
