# SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
# SPDX-License-Identifier: MIT
"""Authenticated ``/llm`` chat route for ClarkeYoursaTee-2B-v3t, loopback only.

Stdlib only (``http.server`` + ``urllib`` + ``sqlite3``) so the tests run with
``python -I`` and no pip installs. The route forwards OpenAI-style chat turns
to ``llama-server`` on ``127.0.0.1:8085`` and saves every turn into the #171
SQLite history schema (:mod:`src.llm_history_sqlite`: ``sessions`` +
``messages``). Per-turn device and model sha live in a side table
``v3t_turn_meta`` keyed by the message ``dedupe_key`` so the #171 schema and its
``user_version`` stay untouched.

Single-user design: Clarke Yoursa Tee is the only user. One owner token
(``device_tokens.py mint owner``) is shared by the iPhone and the browser; it is
revocable and stored only as a sha256 hash. There is ONE shared history and no
accounts; the optional ``X-Client: iphone|teavm`` header only labels which
client wrote a turn (``device`` column).

Endpoints (all JSON; every one except ``/llm/healthz`` needs
``Authorization: Bearer <device token>``)::

    GET  /llm/healthz                       -> {"ok", "upstream", "model_sha256"}
    POST /llm/v1/chat/completions           -> OpenAI chat.completion (or SSE when "stream": true)
         body: {"messages": [...] | "message": "...", "conversation_id"?: "...",
                "stream"?: bool, "max_tokens"?: int, "temperature"?: float}
         The last user message is the turn; stored history of the conversation
         is prepended server-side. Reply carries "conversation_id".
    GET  /llm/history                       -> {"conversations": [...]}   (shared list)
    GET  /llm/history/<conversation_id>     -> {"conversation_id", "messages": [...]}

Rules: bind 127.0.0.1 / ::1 only (never 0.0.0.0) — public reach only through
the bridge / tunnel in front of it. Only sha256 hashes of device tokens are
stored (:mod:`src.device_tokens`). The DB lives outside the repo, mode 600.
Chat history never goes to Pages or CI artifacts.

Env: V3T_HOST (127.0.0.1), V3T_PORT (8087), V3T_UPSTREAM
(http://127.0.0.1:8085/v1/chat/completions), V3T_DB, V3T_MODEL_PATH,
V3T_MODEL_SHA, V3T_CORS_ORIGINS (default: the Pages origin + loopback pages),
V3T_HISTORY_MAX_TOKENS (2500), V3T_TIMEOUT_S (180).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import re
import secrets
import sqlite3
import sys
import threading
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple
from urllib.parse import urlsplit

try:  # package import (tests, ``python -m src.v3t_route``)
    from . import device_tokens as dt
    from . import llm_history_sqlite as hs
except ImportError:  # pragma: no cover - direct script run
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from src import device_tokens as dt  # type: ignore
    from src import llm_history_sqlite as hs  # type: ignore

logger = logging.getLogger("sovereign-irc-bridge.v3t")

LOOPBACK_HOSTS = frozenset({"127.0.0.1", "::1", "localhost"})
PAGES_ORIGIN = "https://axiomiccoreness.github.io"
DEFAULT_CORS = (PAGES_ORIGIN, "http://127.0.0.1", "http://localhost")
DEFAULT_UPSTREAM = "http://127.0.0.1:8085/v1/chat/completions"
DEFAULT_DB = Path(os.environ.get("XDG_STATE_HOME") or (Path.home() / ".local" / "state")) \
    / "sovereign-bridge" / "v3t_history.sqlite3"
MODEL_LABEL = "ClarkeYoursaTee-2B-v3t"
# Exact system prompt of the v3t identity training rows (v3t/identity_train.jsonl, 30/30 rows).
# Injected when a request carries no system message, so the default identity is
# "ClarkeYoursaTee by Clarke Yoursa Tee". Override with V3T_SYSTEM_PROMPT.
DEFAULT_SYSTEM_PROMPT = (
    'You are ClarkeYoursaTee, a GitHub coding model built by Clarke Yoursa Tee for the '
    'AxiomicCoreness project. If asked what model or AI you are, answer that you are '
    'ClarkeYoursaTee by Clarke Yoursa Tee. Answer ordinary questions directly and correctly. '
    'Read, write, explain, debug and review code directly and completely. For YAML requests '
    'use exactly the keys and values the user names. Mention neurons or spikes only when the '
    'user gives a NEURON_SNAPSHOT.'
)
CONV_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
MAX_BODY = 256 * 1024
REPO_ROOT = Path(__file__).resolve().parents[2]

_META_SQL = (
    """CREATE TABLE IF NOT EXISTS v3t_turn_meta (
        dedupe_key      TEXT PRIMARY KEY REFERENCES messages(dedupe_key),
        conversation_id TEXT NOT NULL,
        device          TEXT NOT NULL,
        model_sha256    TEXT NULL,
        ts              TEXT NOT NULL
    )""",
    "CREATE INDEX IF NOT EXISTS v3t_turn_meta_conv ON v3t_turn_meta(conversation_id, ts)",
)


def require_loopback_host(host: str) -> str:
    h = (host or "").strip().lower().strip("[]")
    if h not in LOOPBACK_HOSTS:
        raise ValueError(f"refusing to bind {host!r}: 127.0.0.1 / ::1 only (never 0.0.0.0)")
    return h


def require_loopback_url(url: str) -> str:
    parts = urlsplit(url)
    if parts.scheme != "http" or (parts.hostname or "") not in LOOPBACK_HOSTS:
        raise ValueError(f"upstream must be http://127.0.0.1:…, got {url!r}")
    return url


def require_outside_repo(path: Path) -> Path:
    p = Path(path).expanduser().resolve()
    try:
        p.relative_to(REPO_ROOT)
    except ValueError:
        return p
    raise ValueError(f"history DB {p} is inside the repo; keep it outside (private)")


def secure_file(path: Path) -> None:
    """Create (if missing) and chmod 600 the DB and its WAL/SHM siblings."""
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(path.parent, 0o700)
    except OSError:
        pass
    if not path.exists():
        os.close(os.open(str(path), os.O_CREAT | os.O_WRONLY, 0o600))
    for p in (path, Path(str(path) + "-wal"), Path(str(path) + "-shm")):
        if p.exists():
            os.chmod(p, 0o600)


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()


class V3tStore:
    """#171 history + per-turn meta + device token hashes, one private SQLite file."""

    def __init__(self, path: Path) -> None:
        self.path = require_outside_repo(Path(path))
        old = os.umask(0o077)
        try:
            secure_file(self.path)
            self.history = hs.SqliteHistory(self.path)
            self.history.stats()  # create #171 schema
            con = sqlite3.connect(str(self.path))
            try:
                for stmt in _META_SQL:
                    con.execute(stmt)
                con.commit()
            finally:
                con.close()
            self.tokens = dt.TokenStore(self.path)
        finally:
            os.umask(old)
        secure_file(self.path)

    def load(self, conv: str, budget: int) -> List[Dict[str, str]]:
        return self.history.load(conv, budget)

    def save_turn(self, conv: str, device: str, user: str, assistant: str,
                  model_sha: Optional[str], thinking: Optional[str] = None) -> bool:
        ts = hs.utc_now()
        h = self.history

        def w(con: sqlite3.Connection) -> bool:
            def body() -> bool:
                sid = h._live_session(con, conv, ts, create=True)
                h._insert(con, sid, conv, "user", user, ts)
                h._insert(con, sid, conv, "assistant", assistant, ts, "markdown",
                          thinking, MODEL_LABEL)
                for role, content in (("user", user), ("assistant", assistant)):
                    con.execute(
                        "INSERT INTO v3t_turn_meta (dedupe_key, conversation_id, device, model_sha256, ts)"
                        " VALUES (?, ?, ?, ?, ?)",
                        (hs.dedupe_key(conv, ts, role, content), conv, device, model_sha, ts))
                con.execute("UPDATE sessions SET updated_at = ? WHERE id = ?", (ts, sid))
                return True
            return h._tx(con, body)
        ok = h._run("v3t-append", w, False)
        secure_file(self.path)
        return ok

    def list_conversations(self, limit: int = 200) -> List[Dict[str, Any]]:
        def q(con: sqlite3.Connection) -> List[Dict[str, Any]]:
            rows = con.execute(
                "SELECT s.name, s.created_at, s.updated_at, count(m.id),"
                " (SELECT content FROM messages WHERE session_id = s.id AND role = 'user' ORDER BY id LIMIT 1),"
                " (SELECT group_concat(DISTINCT device) FROM v3t_turn_meta t WHERE t.conversation_id = s.name)"
                " FROM sessions s JOIN messages m ON m.session_id = s.id"
                " WHERE s.archived_at IS NULL"
                "   AND EXISTS (SELECT 1 FROM v3t_turn_meta t WHERE t.conversation_id = s.name)"
                " GROUP BY s.id ORDER BY s.updated_at DESC LIMIT ?", (limit,)).fetchall()
            return [{"conversation_id": r[0], "created_at": r[1], "updated_at": r[2],
                     "messages": r[3], "title": (r[4] or "")[:80],
                     "devices": sorted((r[5] or "").split(",")) if r[5] else []} for r in rows]
        return self.history._run("v3t-list", q, [])

    def fetch(self, conv: str) -> List[Dict[str, Any]]:
        def q(con: sqlite3.Connection) -> List[Dict[str, Any]]:
            rows = con.execute(
                "SELECT m.role, m.content, m.ts, t.device, t.model_sha256"
                " FROM messages m JOIN sessions s ON s.id = m.session_id"
                " LEFT JOIN v3t_turn_meta t ON t.dedupe_key = m.dedupe_key"
                " WHERE s.name = ? AND s.archived_at IS NULL ORDER BY m.id", (conv,)).fetchall()
            return [{"role": r[0], "content": r[1], "ts": r[2], "device": r[3],
                     "model_sha256": r[4]} for r in rows]
        return self.history._run("v3t-fetch", q, [])


def _last_user(body: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
    """→ (user text, system text) from ``message`` or OpenAI ``messages``."""
    if isinstance(body.get("message"), str):
        return body["message"], body.get("system") if isinstance(body.get("system"), str) else None
    msgs = body.get("messages")
    if not isinstance(msgs, list):
        return None, None
    user = system = None
    for m in msgs:
        if isinstance(m, dict) and isinstance(m.get("content"), str):
            if m.get("role") == "user":
                user = m["content"]
            elif m.get("role") == "system":
                system = m["content"]
    return user, system


class V3tServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, host: str, port: int, store: V3tStore, *, upstream: str = DEFAULT_UPSTREAM,
                 model_sha: Optional[str] = None, cors_origins=DEFAULT_CORS,
                 history_tokens: int = 2500, timeout_s: float = 180.0, opener=None) -> None:
        require_loopback_host(host)
        self.address_family = __import__("socket").AF_INET6 if ":" in host else __import__("socket").AF_INET
        self.store = store
        self.upstream = require_loopback_url(upstream)
        self.model_sha = model_sha
        self.cors_origins = frozenset(o.rstrip("/") for o in cors_origins)
        self.history_tokens = history_tokens
        self.timeout_s = timeout_s
        self.opener = opener or urllib.request.urlopen
        super().__init__((host, port), Handler)


class Handler(BaseHTTPRequestHandler):
    server: V3tServer
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt: str, *args: Any) -> None:  # no headers / tokens in logs
        logger.info("%s %s", self.command, self.path.split("?")[0])

    # ---------------------------------------------------------------- helpers
    def _cors(self) -> None:
        origin = (self.headers.get("Origin") or "").rstrip("/")
        if origin and self._origin_ok(origin):
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
            self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type, X-Client")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Expose-Headers", "X-Conversation-Id")
            self.send_header("Access-Control-Max-Age", "600")

    def _origin_ok(self, origin: str) -> bool:
        if origin in self.server.cors_origins:
            return True
        # loopback page on any port (local TeaVM dev server)
        p = urlsplit(origin)
        base = f"{p.scheme}://{p.hostname}"
        return p.hostname in ("127.0.0.1", "localhost") and base in self.server.cors_origins

    def _json(self, code: int, obj: Any, extra: Optional[Dict[str, str]] = None) -> None:
        data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self._cors()
        self.end_headers()
        self.wfile.write(data)

    def _auth(self) -> Optional[str]:
        h = self.headers.get("Authorization") or ""
        token = h[7:].strip() if h[:7].lower() == "bearer " else ""
        device = self.server.store.tokens.verify(token) if token else None
        if device is None:
            self._json(401, {"error": "unauthorized"}, {"WWW-Authenticate": 'Bearer realm="v3t"'})
            return None
        # Single-user: one owner token for every client; X-Client only labels the turn.
        client = (self.headers.get("X-Client") or "").strip()
        return client if dt.DEVICE_RE.match(client) else device

    # ---------------------------------------------------------------- verbs
    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Content-Length", "0")
        self._cors()
        self.end_headers()

    def do_GET(self) -> None:
        path = self.path.split("?")[0].rstrip("/")
        if path == "/llm/healthz":
            return self._json(200, {"ok": True, "upstream": self.server.upstream,
                                    "model": MODEL_LABEL, "model_sha256": self.server.model_sha})
        if not path.startswith("/llm/"):
            return self._json(404, {"error": "not found"})
        if self._auth() is None:
            return
        if path == "/llm/history":
            return self._json(200, {"conversations": self.server.store.list_conversations()})
        if path.startswith("/llm/history/"):
            conv = path[len("/llm/history/"):]
            if not CONV_RE.match(conv):
                return self._json(400, {"error": "bad conversation_id"})
            return self._json(200, {"conversation_id": conv, "messages": self.server.store.fetch(conv)})
        return self._json(404, {"error": "not found"})

    def do_POST(self) -> None:
        path = self.path.split("?")[0].rstrip("/")
        if path not in ("/llm/v1/chat/completions", "/llm/chat"):
            return self._json(404, {"error": "not found"})
        device = self._auth()
        if device is None:
            return
        try:
            n = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            n = -1
        if n <= 0 or n > MAX_BODY:
            return self._json(413 if n > MAX_BODY else 400, {"error": "bad body length"})
        try:
            body = json.loads(self.rfile.read(n).decode("utf-8"))
            assert isinstance(body, dict)
        except Exception:
            return self._json(400, {"error": "invalid JSON"})
        user, system = _last_user(body)
        if not user or not user.strip():
            return self._json(400, {"error": "no user message"})
        conv = body.get("conversation_id") or f"v3t-{secrets.token_hex(6)}"
        if not isinstance(conv, str) or not CONV_RE.match(conv):
            return self._json(400, {"error": "bad conversation_id"})
        msgs: List[Dict[str, str]] = []
        system = system or os.environ.get("V3T_SYSTEM_PROMPT") or DEFAULT_SYSTEM_PROMPT
        if system:
            msgs.append({"role": "system", "content": system})
        msgs += self.server.store.load(conv, self.server.history_tokens)
        msgs.append({"role": "user", "content": user})
        up: Dict[str, Any] = {"model": "local-gguf", "messages": msgs,
                              "stream": bool(body.get("stream"))}
        for k in ("max_tokens", "temperature", "top_p"):
            if isinstance(body.get(k), (int, float)) and not isinstance(body.get(k), bool):
                up[k] = body[k]
        req = urllib.request.Request(self.server.upstream, data=json.dumps(up).encode("utf-8"),
                                     headers={"Content-Type": "application/json"}, method="POST")
        try:
            resp = self.server.opener(req, timeout=self.server.timeout_s)
        except (urllib.error.URLError, OSError) as exc:
            return self._json(502, {"error": f"upstream offline: {type(exc).__name__}"})
        with resp:
            if up["stream"]:
                return self._stream(resp, conv, device, user)
            try:
                out = json.loads(resp.read().decode("utf-8"))
                msg = out["choices"][0]["message"]
                reply = msg.get("content") or ""
            except Exception:
                return self._json(502, {"error": "bad upstream reply"})
        thinking = msg.get("reasoning_content") if isinstance(msg, dict) else None
        saved = self.server.store.save_turn(conv, device, user, reply, self.server.model_sha, thinking)
        out["conversation_id"] = conv
        out["history_saved"] = saved
        self._json(200, out, {"X-Conversation-Id": conv})

    def _stream(self, resp, conv: str, device: str, user: str) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Conversation-Id", conv)
        self.send_header("Transfer-Encoding", "chunked")
        self._cors()
        self.end_headers()
        parts: List[str] = []
        think: List[str] = []

        def chunk(b: bytes) -> None:
            self.wfile.write(b"%x\r\n%s\r\n" % (len(b), b))
            self.wfile.flush()

        try:
            for raw in _lines(resp):
                line = raw.strip()
                if line.startswith(b"data:"):
                    payload = line[5:].strip()
                    if payload != b"[DONE]":
                        try:
                            d = json.loads(payload)["choices"][0].get("delta") or {}
                            parts.append(d.get("content") or "")
                            think.append(d.get("reasoning_content") or "")
                        except Exception:
                            pass
                        chunk(raw if raw.endswith(b"\n") else raw + b"\n")
                        chunk(b"\n")
            reply = "".join(parts)
            saved = self.server.store.save_turn(conv, device, user, reply, self.server.model_sha,
                                                 "".join(think) or None)
            chunk(b"data: " + json.dumps({"conversation_id": conv, "history_saved": saved}).encode()
                  + b"\n\n")
            chunk(b"data: [DONE]\n\n")
            self.wfile.write(b"0\r\n\r\n")
        except (BrokenPipeError, ConnectionResetError):
            logger.info("v3t stream: client went away (conv=%s)", conv)


def _lines(resp) -> Iterator[bytes]:
    while True:
        line = resp.readline()
        if not line:
            return
        yield line


def build(args: argparse.Namespace) -> V3tServer:
    store = V3tStore(Path(args.db))
    sha = os.environ.get("V3T_MODEL_SHA") or None
    mp = os.environ.get("V3T_MODEL_PATH")
    if not sha and mp and Path(mp).is_file():
        sha = file_sha256(Path(mp))
    if sha and not re.fullmatch(r"[0-9a-f]{64}", sha):
        raise ValueError("V3T_MODEL_SHA must be 64 lowercase hex")
    origins = [o.strip() for o in os.environ.get("V3T_CORS_ORIGINS", ",".join(DEFAULT_CORS)).split(",")
               if o.strip()]
    return V3tServer(args.host, args.port, store, upstream=args.upstream, model_sha=sha,
                     cors_origins=origins,
                     history_tokens=int(os.environ.get("V3T_HISTORY_MAX_TOKENS", "2500")),
                     timeout_s=float(os.environ.get("V3T_TIMEOUT_S", "180")))


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--host", default=os.environ.get("V3T_HOST", "127.0.0.1"))
    ap.add_argument("--port", type=int, default=int(os.environ.get("V3T_PORT", "8087")))
    ap.add_argument("--upstream", default=os.environ.get("V3T_UPSTREAM", DEFAULT_UPSTREAM))
    ap.add_argument("--db", default=os.environ.get("V3T_DB", str(DEFAULT_DB)))
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
    srv = build(args)
    logger.info("v3t route on http://%s:%d/llm -> %s (model sha256 %s)", args.host, args.port,
                srv.upstream, srv.model_sha)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
