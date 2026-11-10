# SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
# SPDX-License-Identifier: MIT
"""paper_mcp store, JSON-RPC, CLI, and loopback HTTP."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import urllib.error
import urllib.request
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
from paper_mcp.server import (  # noqa: E402
    DEFAULT_BIND,
    CanvasError,
    CanvasStore,
    handle_message,
    make_http_server,
    resolve_loopback_host,
    serve_stdio,
)


def _env(root: Path) -> dict:
    env = os.environ.copy()
    env.pop("PAPER_MCP_ROOT", None)
    env.pop("PAPER_MCP_MAX_BYTES", None)
    env["PYTHONPATH"] = str(ROOT)
    env["PAPER_MCP_ROOT"] = str(root)
    return env


def _run(root: Path, args, input_text=None):
    return subprocess.run(
        [sys.executable, "-m", "paper_mcp", "--root", str(root), *args],
        input=input_text,
        capture_output=True,
        text=True,
        cwd=str(ROOT),
        env=_env(root),
        check=False,
    )


def _rpc(store, msg_id, method, params=None):
    message = {"jsonrpc": "2.0", "id": msg_id, "method": method}
    if params is not None:
        message["params"] = params
    return handle_message(store, message)


def test_initialize_tools_ping_and_notifications(tmp_path):
    store = CanvasStore(tmp_path / "c")
    init = _rpc(
        store,
        1,
        "initialize",
        {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "t", "version": "0"}},
    )
    assert init["result"]["protocolVersion"] == "2024-11-05"
    assert init["result"]["serverInfo"]["name"] == "paper-mcp"
    names = [tool["name"] for tool in _rpc(store, 2, "tools/list")["result"]["tools"]]
    assert names == [
        "canvas_list",
        "canvas_read",
        "canvas_write",
        "canvas_delete",
        "canvas_patch",
    ]
    assert _rpc(store, "p", "ping")["result"] == {}
    assert handle_message(store, {"jsonrpc": "2.0", "method": "notifications/initialized"}) is None
    assert handle_message(
        store, {"jsonrpc": "2.0", "method": "notifications/cancelled", "params": {"requestId": 1}}
    ) is None
    assert handle_message(store, {"jsonrpc": "2.0", "id": 9, "result": {}}) is None
    missing = _rpc(store, 3, "no/such")
    assert missing["error"]["code"] == -32601


def test_tool_roundtrip_resources_and_stdio(tmp_path):
    store = CanvasStore(tmp_path / "c")
    wrote = _rpc(
        store,
        1,
        "tools/call",
        {"name": "canvas_write", "arguments": {"name": "board.html", "content": "<p>one</p>"}},
    )
    assert wrote["result"]["isError"] is False
    listed = json.loads(
        _rpc(store, 2, "tools/call", {"name": "canvas_list", "arguments": {}})["result"]["content"][0]["text"]
    )
    assert listed == ["board.html"]
    text = _rpc(
        store, 3, "tools/call", {"name": "canvas_read", "arguments": {"name": "board.html"}}
    )["result"]["content"][0]["text"]
    assert text == "<p>one</p>"
    patched = _rpc(
        store,
        4,
        "tools/call",
        {
            "name": "canvas_patch",
            "arguments": {"name": "board.html", "find": "one", "replace": "two"},
        },
    )
    assert json.loads(patched["result"]["content"][0]["text"])["replacements"] == 1
    resources = _rpc(store, 5, "resources/list")["result"]["resources"]
    assert resources[0]["uri"] == "canvas://board.html"
    assert resources[0]["mimeType"] == "text/html"
    body = _rpc(store, 6, "resources/read", {"uri": "canvas://board.html"})["result"]["contents"][0]
    assert "two" in body["text"]
    deleted = _rpc(
        store, 7, "tools/call", {"name": "canvas_delete", "arguments": {"name": "board.html"}}
    )
    assert deleted["result"]["isError"] is False
    missing = _rpc(
        store, 8, "tools/call", {"name": "canvas_read", "arguments": {"name": "board.html"}}
    )
    assert missing["result"]["isError"] is True

    raw_in = (
        b'{"jsonrpc":"2.0","id":1,"method":"ping"}\n'
        b'{"jsonrpc":"2.0","method":"notifications/initialized"}\n'
        b"not-json\n"
    )
    stdin = _Bytes()
    stdin.write(raw_in)
    stdin.seek(0)
    stdout = _Bytes()
    serve_stdio(store, stdin, stdout)
    lines = [json.loads(line) for line in stdout.getvalue().splitlines() if line.strip()]
    assert lines[0]["result"] == {}
    assert lines[1]["error"]["code"] == -32700
    assert len(lines) == 2


class _Bytes:
    """Minimal binary stream for serve_stdio."""

    def __init__(self):
        self._buf = bytearray()
        self._pos = 0

    def write(self, data):
        if self._pos != len(self._buf):
            del self._buf[self._pos :]
        self._buf.extend(data)
        self._pos = len(self._buf)
        return len(data)

    def read(self, n=-1):
        if n < 0:
            n = len(self._buf) - self._pos
        chunk = bytes(self._buf[self._pos : self._pos + n])
        self._pos += len(chunk)
        return chunk

    def readline(self):
        rest = bytes(self._buf[self._pos :])
        if not rest:
            return b""
        nl = rest.find(b"\n")
        if nl < 0:
            self._pos = len(self._buf)
            return rest
        chunk = rest[: nl + 1]
        self._pos += len(chunk)
        return chunk

    def seek(self, pos):
        self._pos = pos

    def getvalue(self):
        return bytes(self._buf)

    def flush(self):
        return None


def test_path_guards_size_and_atomic_replace(tmp_path):
    root = tmp_path / "c"
    outside = tmp_path / "secret.html"
    outside.write_text("secret", encoding="utf-8")
    store = CanvasStore(root, max_bytes=32)
    store.write("ok.html", "<p>ok</p>")
    for bad in ("../secret.html", "/etc/passwd", "sub/x.html", "..", "", "foo.bar", ".hidden.html", "a.py"):
        with pytest.raises(CanvasError):
            store.write(bad, "<p>x</p>")
    link = root / "link.html"
    link.symlink_to(outside)
    with pytest.raises(CanvasError):
        store.read("link.html")
    with pytest.raises(CanvasError):
        store.write("link.html", "<p>x</p>")
    assert outside.read_text(encoding="utf-8") == "secret"
    assert "link.html" not in store.list_canvases()
    with pytest.raises(CanvasError):
        store.write("big.html", "x" * 33)
    assert (root / "ok.html").read_text(encoding="utf-8") == "<p>ok</p>"
    store.write("ok.html", "<p>next</p>")
    assert not list(root.glob(".write-*"))
    with pytest.raises(CanvasError):
        store.patch("ok.html", "missing", "z")
    assert (root / "ok.html").read_text(encoding="utf-8") == "<p>next</p>"
    with pytest.raises(CanvasError):
        store.write("data.json", "{")
    store.write("data.json", '{"a": 1}')
    store.patch("data.json", "1", "2")
    assert json.loads((root / "data.json").read_text(encoding="utf-8")) == {"a": 2}


def test_every_cli_subcommand(tmp_path):
    root = tmp_path / "cli"
    html = tmp_path / "in.html"
    html.write_text("<svg></svg>", encoding="utf-8")

    empty = _run(root, ["serve"], input_text="")
    assert empty.returncode == 0
    assert empty.stdout == ""

    ping = _run(
        root,
        ["serve"],
        input_text='{"jsonrpc":"2.0","id":1,"method":"tools/list"}\n',
    )
    assert ping.returncode == 0
    assert "canvas_write" in ping.stdout

    default = _run(
        root,
        [],
        input_text='{"jsonrpc":"2.0","id":7,"method":"ping"}\n',
    )
    assert default.returncode == 0
    assert json.loads(default.stdout)["result"] == {}

    wrote = _run(root, ["write", "pic.svg", "--file", str(html)])
    assert wrote.returncode == 0
    assert "wrote pic.svg" in wrote.stdout
    piped = _run(root, ["--json", "write", "note.txt"], input_text="hello\n")
    assert piped.returncode == 0
    assert json.loads(piped.stdout)["ok"] is True

    listed = _run(root, ["list"])
    assert listed.returncode == 0
    assert listed.stdout.splitlines() == ["note.txt", "pic.svg"]
    as_json = _run(root, ["list", "--json"])
    assert json.loads(as_json.stdout)["canvases"] == ["note.txt", "pic.svg"]

    read = _run(root, ["read", "note.txt"])
    assert read.stdout == "hello\n"
    read_json = _run(root, ["read", "pic.svg", "--json"])
    body = json.loads(read_json.stdout)
    assert body["mimeType"] == "image/svg+xml"
    assert body["content"] == "<svg></svg>"

    resources = _run(root, ["resources"])
    assert "canvas://note.txt" in resources.stdout
    resources_json = _run(root, ["resources", "--json"])
    assert len(json.loads(resources_json.stdout)["resources"]) == 2

    patched = _run(root, ["patch", "note.txt", "--find", "hello", "--replace", "world"])
    assert patched.returncode == 0
    assert _run(root, ["read", "note.txt"]).stdout == "world\n"

    removed = _run(root, ["delete", "note.txt"])
    assert removed.returncode == 0
    missing = _run(root, ["delete", "note.txt"])
    assert missing.returncode == 1

    env_root = tmp_path / "from-env"
    env = _env(env_root)
    proc = subprocess.run(
        [sys.executable, "-m", "paper_mcp", "write", "a.md", "--file", str(html)],
        capture_output=True,
        text=True,
        cwd=str(tmp_path),
        env=env,
        check=False,
    )
    assert proc.returncode == 0
    assert (env_root / "a.md").is_file()


def test_serve_http_cli_and_loopback_cors(tmp_path):
    assert DEFAULT_BIND == "127.0.0.1"
    assert resolve_loopback_host(None) == "127.0.0.1"
    assert resolve_loopback_host("localhost") == "127.0.0.1"
    for refused in ("0.0.0.0", "::", "[::]", "*", "10.0.0.8"):
        with pytest.raises(SystemExit):
            resolve_loopback_host(refused)

    refused = _run(tmp_path / "unused", ["serve-http", "--bind", "0.0.0.0", "--port", "9"])
    assert refused.returncode == 1
    assert "0.0.0.0" in refused.stderr

    store = CanvasStore(tmp_path / "http")
    server = make_http_server(store, port=0)
    assert server.server_address[0] == "127.0.0.1"
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        port = server.server_address[1]
        base = "http://127.0.0.1:{0}".format(port)
        origin = "https://canvas.example"
        pre = urllib.request.Request(
            base + "/mcp",
            method="OPTIONS",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type, Authorization",
            },
        )
        with urllib.request.urlopen(pre) as resp:
            assert resp.status == 204
            assert resp.headers["Access-Control-Allow-Origin"] == origin
            assert "POST" in resp.headers["Access-Control-Allow-Methods"]
            assert "GET" in resp.headers["Access-Control-Allow-Methods"]
            assert "OPTIONS" in resp.headers["Access-Control-Allow-Methods"]
            allow_headers = resp.headers["Access-Control-Allow-Headers"]
            assert "Content-Type" in allow_headers
            assert "Authorization" in allow_headers
            assert resp.headers["Vary"] == "Origin"

        payload = json.dumps(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "canvas_write",
                    "arguments": {"name": "cross.html", "content": "<p>cross</p>"},
                },
            }
        ).encode("utf-8")
        post = urllib.request.Request(
            base + "/mcp",
            data=payload,
            method="POST",
            headers={"Origin": origin, "Content-Type": "application/json"},
        )
        with urllib.request.urlopen(post) as resp:
            assert resp.headers["Access-Control-Allow-Origin"] == origin
            assert resp.headers["Vary"] == "Origin"
            body = json.loads(resp.read().decode("utf-8"))
        assert body["result"]["isError"] is False
        assert (tmp_path / "http" / "cross.html").read_text(encoding="utf-8") == "<p>cross</p>"

        health = urllib.request.Request(
            base + "/healthz",
            headers={"Origin": origin},
        )
        with urllib.request.urlopen(health) as resp:
            assert json.loads(resp.read().decode("utf-8"))["status"] == "ok"
            assert resp.headers["Cross-Origin-Resource-Policy"] == "cross-origin"
            assert resp.headers["Access-Control-Allow-Origin"] == origin
    finally:
        server.shutdown()
        server.server_close()

    star = make_http_server(CanvasStore(tmp_path / "star"), port=0, cors_origin="*")
    thread = threading.Thread(target=star.serve_forever, daemon=True)
    thread.start()
    try:
        req = urllib.request.Request(
            "http://127.0.0.1:{0}/healthz".format(star.server_address[1]),
            headers={"Origin": "https://anywhere.example"},
        )
        with urllib.request.urlopen(req) as resp:
            assert resp.headers["Access-Control-Allow-Origin"] == "*"
            assert resp.headers["Vary"] == "Origin"
    finally:
        star.shutdown()
        star.server_close()

    proc = subprocess.Popen(
        [sys.executable, "-m", "paper_mcp", "--root", str(tmp_path / "cli-http"), "serve-http", "--port", "0"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=str(ROOT),
        env=_env(tmp_path / "cli-http"),
    )
    try:
        line = proc.stdout.readline()
        assert line.startswith("paper_mcp http listening on 127.0.0.1 ")
        port = int(line.split()[-1])
        with urllib.request.urlopen("http://127.0.0.1:{0}/healthz".format(port)) as resp:
            assert json.loads(resp.read().decode("utf-8"))["service"] == "paper-mcp"
    finally:
        proc.terminate()
        proc.wait(timeout=10)


def test_import_without_cwd_on_path(tmp_path):
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT)
    compiled = subprocess.run(
        [
            sys.executable,
            "-I",
            "-m",
            "py_compile",
            "paper_mcp/__init__.py",
            "paper_mcp/__main__.py",
            "paper_mcp/server.py",
            "paper_mcp/cli.py",
            "tests/test_paper_mcp.py",
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert compiled.returncode == 0, compiled.stderr
    imported = subprocess.run(
        [
            sys.executable,
            "-P",
            "-c",
            "import paper_mcp, paper_mcp.cli, paper_mcp.server; print(paper_mcp.__version__)",
        ],
        cwd=str(tmp_path),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert imported.returncode == 0, imported.stderr
    assert imported.stdout.strip() == "0.1.0"


def test_cli_rejects_escape(tmp_path):
    root = tmp_path / "c"
    CanvasStore(root).write("ok.txt", "a")
    escaped = _run(root, ["read", "../ok.txt"])
    assert escaped.returncode != 0
