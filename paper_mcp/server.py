# SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
# SPDX-License-Identifier: MIT
"""Paper canvas store and Model Context Protocol (JSON-RPC 2.0) server.

Stdlib only. Canvases are text files (HTML, SVG, JSON, Markdown, plain text)
under ``PAPER_MCP_ROOT`` (default ``./.paper_canvases``).

The HTTP transport binds like ``tools/cors-anywhere/server.js`` (PR #129,
loopback only) and serves ``GET /healthz`` as a public probe with
``Cross-Origin-Resource-Policy: cross-origin``, the same idea as the
hardened port380 ``/healthz`` route.
"""

from __future__ import annotations

import json
import os
import re
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, List, Optional

__all__ = [
    "DEFAULT_BIND",
    "DEFAULT_MAX_BYTES",
    "DEFAULT_ROOT",
    "PROTOCOL_VERSION",
    "CanvasError",
    "CanvasStore",
    "handle_message",
    "make_http_server",
    "resolve_loopback_host",
    "serve_stdio",
]

PROTOCOL_VERSION = "2024-11-05"
SUPPORTED_PROTOCOLS = (
    "2024-11-05",
    "2025-03-26",
    "2025-06-18",
)
SERVER_NAME = "paper-mcp"
SERVER_VERSION = "0.1.0"
DEFAULT_ROOT = Path("./.paper_canvases")
DEFAULT_MAX_BYTES = 1024 * 1024
DEFAULT_BIND = "127.0.0.1"
DEFAULT_HTTP_PORT = 8765

# Single path segment. Extension, when present, is a canvas text type.
_NAME_RE = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}(?:\.(?:html|svg|json|txt|md))?$"
)
_ORIGIN_RE = re.compile(r"[\r\n\x00]")
_MIME = {
    ".html": "text/html",
    ".svg": "image/svg+xml",
    ".json": "application/json",
    ".txt": "text/plain",
    ".md": "text/markdown",
}


class CanvasError(Exception):
    """Rejected canvas name, missing file, or store limit."""


def _mime(name: str) -> str:
    return _MIME.get(Path(name).suffix.lower(), "text/plain")


class CanvasStore:
    """Atomic, path-checked canvas directory."""

    def __init__(self, root: Path, max_bytes: int = DEFAULT_MAX_BYTES) -> None:
        if max_bytes < 1:
            raise CanvasError("max_bytes must be positive")
        self.root = Path(root)
        self.max_bytes = int(max_bytes)
        self._lock = threading.Lock()

    @classmethod
    def from_env(cls, root: Optional[str] = None) -> "CanvasStore":
        chosen = root if root else os.environ.get("PAPER_MCP_ROOT", "")
        path = Path(chosen) if chosen else DEFAULT_ROOT
        raw_max = os.environ.get("PAPER_MCP_MAX_BYTES", "").strip()
        max_bytes = int(raw_max) if raw_max else DEFAULT_MAX_BYTES
        return cls(path, max_bytes=max_bytes)

    def resolved_root(self) -> Path:
        self.root.mkdir(parents=True, exist_ok=True)
        resolved = self.root.resolve()
        if not resolved.is_dir():
            raise CanvasError("canvas root is not a directory")
        return resolved

    def validate_name(self, name: Any) -> str:
        if not isinstance(name, str) or name != name.strip() or not name:
            raise CanvasError("canvas name must be a non-empty string")
        if "\x00" in name or "/" in name or "\\" in name or ".." in name:
            raise CanvasError("canvas name rejected")
        if Path(name).is_absolute():
            raise CanvasError("absolute canvas paths are rejected")
        if not _NAME_RE.fullmatch(name):
            raise CanvasError(
                "canvas name must be a single segment "
                "(optional .html, .svg, .json, .txt, or .md)"
            )
        return name

    def _path(self, name: str) -> Path:
        safe = self.validate_name(name)
        root = self.resolved_root()
        path = root / safe
        if path.is_symlink():
            raise CanvasError("symlink canvases are rejected")
        if path.exists() and not path.is_file():
            raise CanvasError("canvas name is not a file")
        parent = path.parent.resolve()
        if parent != root:
            raise CanvasError("canvas path escapes the store")
        if path.exists():
            resolved = path.resolve()
            try:
                resolved.relative_to(root)
            except ValueError as exc:
                raise CanvasError("canvas path escapes the store") from exc
            if resolved.parent != root:
                raise CanvasError("canvas path escapes the store")
        return path

    def list_canvases(self) -> List[str]:
        with self._lock:
            root = self.resolved_root()
            names: List[str] = []
            for entry in root.iterdir():
                if entry.name.startswith(".") or entry.is_symlink():
                    continue
                if not entry.is_file():
                    continue
                try:
                    self.validate_name(entry.name)
                except CanvasError:
                    continue
                names.append(entry.name)
            names.sort()
            return names

    def read(self, name: str) -> str:
        with self._lock:
            path = self._path(name)
            if not path.is_file():
                raise CanvasError("canvas not found: {0}".format(name))
            data = path.read_bytes()
            if len(data) > self.max_bytes:
                raise CanvasError("canvas exceeds size limit")
            try:
                return data.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise CanvasError("canvas is not UTF-8 text") from exc

    def write(self, name: str, content: Any) -> Dict[str, Any]:
        text = self._as_text(name, content)
        data = text.encode("utf-8")
        self._check_size(data)
        with self._lock:
            path = self._path(name)
            self._atomic_write(path, data)
        return {"name": name, "bytes": len(data), "mimeType": _mime(name)}

    def delete(self, name: str) -> Dict[str, Any]:
        with self._lock:
            path = self._path(name)
            if path.is_symlink():
                raise CanvasError("symlink canvases are rejected")
            if not path.is_file():
                raise CanvasError("canvas not found: {0}".format(name))
            path.unlink()
        return {"name": name, "deleted": True}

    def patch(self, name: str, find: Any, replace: Any) -> Dict[str, Any]:
        if not isinstance(find, str) or find == "":
            raise CanvasError("find must be a non-empty string")
        if not isinstance(replace, str):
            raise CanvasError("replace must be a string")
        with self._lock:
            path = self._path(name)
            if not path.is_file():
                raise CanvasError("canvas not found: {0}".format(name))
            current = path.read_bytes()
            if len(current) > self.max_bytes:
                raise CanvasError("canvas exceeds size limit")
            try:
                text = current.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise CanvasError("canvas is not UTF-8 text") from exc
            count = text.count(find)
            if count == 0:
                raise CanvasError("find text not present")
            updated = text.replace(find, replace)
            checked = self._as_text(name, updated)
            data = checked.encode("utf-8")
            self._check_size(data)
            self._atomic_write(path, data)
        return {
            "name": name,
            "replacements": count,
            "bytes": len(data),
            "mimeType": _mime(name),
        }

    def resources(self) -> List[Dict[str, str]]:
        items = []
        for name in self.list_canvases():
            items.append(
                {
                    "uri": "canvas://{0}".format(name),
                    "name": name,
                    "mimeType": _mime(name),
                }
            )
        return items

    def read_resource(self, uri: Any) -> Dict[str, str]:
        name = _uri_name(uri)
        return {
            "uri": "canvas://{0}".format(name),
            "mimeType": _mime(name),
            "text": self.read(name),
        }

    def _as_text(self, name: str, content: Any) -> str:
        self.validate_name(name)
        if not isinstance(content, str):
            raise CanvasError("content must be a string")
        if "\x00" in content:
            raise CanvasError("content must be text")
        if name.endswith(".json"):
            try:
                json.loads(content)
            except json.JSONDecodeError as exc:
                raise CanvasError("JSON canvas is not valid JSON") from exc
        return content

    def _check_size(self, data: bytes) -> None:
        if len(data) > self.max_bytes:
            raise CanvasError(
                "content exceeds {0} bytes".format(self.max_bytes)
            )

    def _atomic_write(self, path: Path, data: bytes) -> None:
        if path.is_symlink():
            raise CanvasError("symlink canvases are rejected")
        directory = path.parent
        fd, tmp_name = tempfile.mkstemp(
            prefix=".write-", suffix=".tmp", dir=str(directory)
        )
        tmp = Path(tmp_name)
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            if path.is_symlink():
                raise CanvasError("symlink canvases are rejected")
            os.replace(str(tmp), str(path))
        finally:
            if tmp.exists():
                try:
                    tmp.unlink()
                except OSError:
                    pass


def _uri_name(uri: Any) -> str:
    if not isinstance(uri, str) or not uri.startswith("canvas://"):
        raise CanvasError("resource uri must start with canvas://")
    return uri[len("canvas://"):]


def _tool_schemas() -> List[Dict[str, Any]]:
    name_prop = {
        "type": "string",
        "description": "Canvas file name, one path segment.",
    }
    return [
        {
            "name": "canvas_list",
            "description": "List canvases in the store.",
            "inputSchema": {
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
        },
        {
            "name": "canvas_read",
            "description": "Read one canvas as UTF-8 text.",
            "inputSchema": {
                "type": "object",
                "properties": {"name": name_prop},
                "required": ["name"],
                "additionalProperties": False,
            },
        },
        {
            "name": "canvas_write",
            "description": "Create or replace a canvas (HTML, SVG, or JSON text).",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "name": name_prop,
                    "content": {"type": "string"},
                },
                "required": ["name", "content"],
                "additionalProperties": False,
            },
        },
        {
            "name": "canvas_delete",
            "description": "Delete one canvas.",
            "inputSchema": {
                "type": "object",
                "properties": {"name": name_prop},
                "required": ["name"],
                "additionalProperties": False,
            },
        },
        {
            "name": "canvas_patch",
            "description": "Replace every occurrence of find with replace.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "name": name_prop,
                    "find": {"type": "string"},
                    "replace": {"type": "string"},
                },
                "required": ["name", "find", "replace"],
                "additionalProperties": False,
            },
        },
    ]


def _call_tool(store: CanvasStore, name: str, arguments: Any) -> Dict[str, Any]:
    if arguments is None:
        arguments = {}
    if not isinstance(arguments, dict):
        raise CanvasError("tool arguments must be an object")
    if name == "canvas_list":
        payload = store.list_canvases()
        text = json.dumps(payload)
    elif name == "canvas_read":
        text = store.read(arguments.get("name"))
    elif name == "canvas_write":
        text = json.dumps(
            store.write(arguments.get("name"), arguments.get("content"))
        )
    elif name == "canvas_delete":
        text = json.dumps(store.delete(arguments.get("name")))
    elif name == "canvas_patch":
        text = json.dumps(
            store.patch(
                arguments.get("name"),
                arguments.get("find"),
                arguments.get("replace"),
            )
        )
    else:
        raise CanvasError("unknown tool: {0}".format(name))
    return {"content": [{"type": "text", "text": text}], "isError": False}


def _ok(msg_id: Any, result: Any) -> Dict[str, Any]:
    return {"jsonrpc": "2.0", "id": msg_id, "result": result}


def _err(msg_id: Any, code: int, message: str) -> Dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": msg_id,
        "error": {"code": code, "message": message},
    }


def handle_message(store: CanvasStore, message: Any) -> Optional[Dict[str, Any]]:
    """Handle one JSON-RPC message. Notifications return None."""
    if not isinstance(message, dict):
        return _err(None, -32600, "Invalid Request")
    method = message.get("method")
    msg_id = message.get("id", None)
    has_id = "id" in message and msg_id is not None
    if not isinstance(method, str):
        # Inbound responses and empty notes are not requests.
        if "result" in message or "error" in message or not has_id:
            return None
        return _err(msg_id, -32600, "Invalid Request")
    if method.startswith("notifications/") or not has_id:
        return None
    params = message.get("params", {})
    if params is None:
        params = {}
    try:
        if method == "initialize":
            if not isinstance(params, dict):
                return _err(msg_id, -32602, "Invalid params")
            client_version = str(params.get("protocolVersion") or "")
            version = client_version if client_version in SUPPORTED_PROTOCOLS else PROTOCOL_VERSION
            return _ok(
                msg_id,
                {
                    "protocolVersion": version,
                    "capabilities": {
                        "tools": {"listChanged": False},
                        "resources": {"subscribe": False, "listChanged": False},
                    },
                    "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
                    "instructions": (
                        "Filesystem canvases. Tools: canvas_list, canvas_read, "
                        "canvas_write, canvas_delete, canvas_patch."
                    ),
                },
            )
        if method == "ping":
            return _ok(msg_id, {})
        if method == "tools/list":
            return _ok(msg_id, {"tools": _tool_schemas()})
        if method == "tools/call":
            if not isinstance(params, dict) or not isinstance(params.get("name"), str):
                return _err(msg_id, -32602, "Invalid params")
            try:
                result = _call_tool(store, params["name"], params.get("arguments"))
            except CanvasError as exc:
                return _ok(
                    msg_id,
                    {
                        "content": [{"type": "text", "text": str(exc)}],
                        "isError": True,
                    },
                )
            return _ok(msg_id, result)
        if method == "resources/list":
            return _ok(msg_id, {"resources": store.resources()})
        if method == "resources/read":
            if not isinstance(params, dict):
                return _err(msg_id, -32602, "Invalid params")
            try:
                body = store.read_resource(params.get("uri"))
            except CanvasError as exc:
                return _err(msg_id, -32002, str(exc))
            return _ok(msg_id, {"contents": [body]})
        return _err(msg_id, -32601, "Method not found")
    except CanvasError as exc:
        return _err(msg_id, -32000, str(exc))


def serve_stdio(store: CanvasStore, stdin: Any = None, stdout: Any = None) -> None:
    """Newline-delimited JSON-RPC on stdio. Logs stay off stdout."""
    if stdin is None:
        stdin = sys.stdin.buffer
    if stdout is None:
        stdout = sys.stdout.buffer
    while True:
        line = stdin.readline()
        if not line:
            return
        stripped = line.strip()
        if not stripped:
            continue
        try:
            message = json.loads(stripped.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            response: Optional[Dict[str, Any]] = _err(None, -32700, "Parse error")
        else:
            response = handle_message(store, message)
        if response is None:
            continue
        payload = json.dumps(response, ensure_ascii=False).encode("utf-8")
        stdout.write(payload + b"\n")
        stdout.flush()


def resolve_loopback_host(host: Optional[str]) -> str:
    """Bind policy copied from tools/cors-anywhere/server.js.

    Listen address is always 127.0.0.1. ``0.0.0.0``, ``::``, ``*``, and any
    other host are refused. ``localhost`` is accepted as an alias.
    """
    raw = DEFAULT_BIND if host is None or host.strip() == "" else host.strip()
    if (
        raw == "0.0.0.0"
        or raw == "::"
        or raw == "[::]"
        or raw == "*"
        or (raw != "127.0.0.1" and raw != "localhost")
    ):
        raise SystemExit(
            "FATAL: refuse bind host {0}; only 127.0.0.1 "
            "(or localhost) is allowed".format(raw)
        )
    return "127.0.0.1"


def _cors_value(mode: Optional[str], origin: Optional[str]) -> Optional[str]:
    if mode == "*":
        return "*"
    if origin is None:
        return None
    if _ORIGIN_RE.search(origin) or origin.strip() == "" or len(origin) > 256:
        return None
    if mode is None:
        return origin
    if origin == mode:
        return origin
    return None


class _CanvasHandler(BaseHTTPRequestHandler):
    server_version = "paper-mcp/" + SERVER_VERSION
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt: str, *args: Any) -> None:
        sys.stderr.write(
            "%s - %s\n" % (self.address_string(), fmt % args)
        )

    def _cors_headers(self) -> List[tuple]:
        origin = self.headers.get("Origin")
        allow = _cors_value(getattr(self.server, "cors_origin", None), origin)
        headers = [
            ("Vary", "Origin"),
            ("Access-Control-Allow-Methods", "GET, POST, OPTIONS"),
            ("Access-Control-Allow-Headers", "Content-Type, Authorization"),
        ]
        if allow is not None:
            headers.append(("Access-Control-Allow-Origin", allow))
        return headers

    def _write(self, code: int, body: bytes, content_type: str, extra: Optional[List[tuple]] = None) -> None:
        self.send_response(code)
        for key, value in self._cors_headers():
            self.send_header(key, value)
        path = self.path.split("?", 1)[0]
        if path == "/healthz":
            self.send_header("Cross-Origin-Resource-Policy", "cross-origin")
        if extra:
            for key, value in extra:
                self.send_header(key, value)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        if body:
            self.wfile.write(body)

    def _json(self, code: int, payload: Any) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self._write(code, body, "application/json; charset=utf-8")

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        for key, value in self._cors_headers():
            self.send_header(key, value)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        path = self.path.split("?", 1)[0]
        if path == "/healthz":
            # Public probe. No secrets. CORP cross-origin so a browser
            # Origin can read it, matching the port380 /healthz override.
            self._json(200, {"status": "ok", "service": SERVER_NAME})
            return
        self._json(404, {"error": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        path = self.path.split("?", 1)[0]
        if path != "/mcp":
            self._json(404, {"error": "not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._json(400, _err(None, -32700, "Parse error"))
            return
        max_body = int(getattr(self.server, "max_body", DEFAULT_MAX_BYTES + 65536))
        if length < 0 or length > max_body:
            self._json(413, {"error": "body too large"})
            return
        raw = self.rfile.read(length) if length else b""
        try:
            message = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._json(400, _err(None, -32700, "Parse error"))
            return
        response = handle_message(self.server.store, message)  # type: ignore[attr-defined]
        if response is None:
            self.send_response(204)
            for key, value in self._cors_headers():
                self.send_header(key, value)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        self._json(200, response)


class CanvasHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, store: CanvasStore, server_address: tuple, cors_origin: Optional[str]) -> None:
        self.store = store
        self.cors_origin = cors_origin
        self.max_body = store.max_bytes + 65536
        super().__init__(server_address, _CanvasHandler)


def make_http_server(
    store: CanvasStore,
    host: Optional[str] = None,
    port: int = DEFAULT_HTTP_PORT,
    cors_origin: Optional[str] = None,
) -> CanvasHTTPServer:
    bind = resolve_loopback_host(host)
    if port < 0 or port > 65535:
        raise SystemExit("FATAL: port must be 0-65535")
    return CanvasHTTPServer(store, (bind, int(port)), cors_origin)
