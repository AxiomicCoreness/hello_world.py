# SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
# SPDX-License-Identifier: MIT
"""tools/paper-mcp mirrors tools/cors-anywhere. Serve is not started when paper_mcp is absent."""
from __future__ import annotations

import importlib.util
import json
import os
import socket
import subprocess
import sys
import urllib.request
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "paper-mcp"
LAUNCH = ROOT / "scripts" / "paper_mcp.sh"


def _bash(args, env=None, timeout=30):
    merged = os.environ.copy()
    merged.pop("PAPER_MCP_BIND", None)
    merged.pop("BIND_HOST", None)
    merged.pop("HOST", None)
    if env:
        merged.update(env)
    return subprocess.run(
        ["bash", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=timeout,
        env=merged,
    )


def test_tree_matches_cors_anywhere_shape():
    for name in ("README.md", "help.txt", "launch.sh", "config.env", ".gitignore"):
        assert (TOOL / name).is_file(), name
    assert (ROOT / "tools" / "cors-anywhere" / "README.md").is_file()
    assert (ROOT / "tools" / "cors-anywhere" / "help.txt").is_file()
    readme = (TOOL / "README.md").read_text(encoding="utf-8")
    for needle in (
        "tools/paper-mcp/",
        "scripts/paper_mcp.sh",
        "sovereign/__main__.py",
        "sovereign/paper_mcp.py",
        "127.0.0.1",
        "/healthz",
        "PAPER_MCP_ROOT",
    ):
        assert needle in readme
    help_txt = (TOOL / "help.txt").read_text(encoding="utf-8")
    assert "127.0.0.1" in help_txt
    assert "/healthz" in help_txt
    assert "0.0.0.0" in help_txt


def test_scripts_pass_bash_n():
    for rel in ("scripts/paper_mcp.sh", "tools/paper-mcp/launch.sh"):
        proc = _bash(["-n", str(ROOT / rel)])
        assert proc.returncode == 0, proc.stderr


def test_non_loopback_bind_is_refused():
    proc = _bash([str(LAUNCH), "serve-http"], env={"HOST": "0.0.0.0"})
    assert proc.returncode == 1
    assert "FATAL" in proc.stderr
    assert "0.0.0.0" in proc.stderr


def test_help_does_not_need_the_package():
    proc = _bash([str(LAUNCH), "--help"])
    assert proc.returncode == 0
    assert "serve-http" in proc.stderr


def test_serve_without_package_exits_before_listen():
    if importlib.util.find_spec("paper_mcp") is not None:
        pytest.skip("paper_mcp is importable; serve would listen on stdio")
    proc = _bash(
        [str(LAUNCH), "serve"],
        env={"PAPER_MCP_ROOT": "/tmp/paper-mcp-absent-root"},
    )
    assert proc.returncode == 1
    assert "paper_mcp" in proc.stderr


def test_serve_http_healthz_on_loopback(tmp_path):
    if importlib.util.find_spec("paper_mcp") is None:
        pytest.skip("paper_mcp is not importable on this checkout")
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    proc = subprocess.Popen(
        ["bash", str(LAUNCH), "serve-http"],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env={
            **os.environ,
            "PAPER_MCP_ROOT": str(tmp_path / "canvases"),
            "PAPER_MCP_PORT": str(port),
            "PAPER_MCP_BIND": "127.0.0.1",
            "HOST": "127.0.0.1",
        },
    )
    try:
        line = proc.stdout.readline()
        assert line.startswith("paper_mcp http listening on 127.0.0.1 "), line
        assert int(line.split()[-1]) == port
        with urllib.request.urlopen(
            "http://127.0.0.1:{0}/healthz".format(port), timeout=5
        ) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            assert body == {"status": "ok", "service": "paper-mcp"}
            assert resp.headers["Cross-Origin-Resource-Policy"] == "cross-origin"
    finally:
        proc.terminate()
        proc.wait(timeout=10)


def test_launch_sh_keeps_caller_bind():
    proc = _bash(
        [str(ROOT / "tools" / "paper-mcp" / "launch.sh"), "serve-http"],
        env={"HOST": "0.0.0.0", "PAPER_MCP_BIND": "0.0.0.0"},
    )
    assert proc.returncode == 1
    assert "FATAL" in proc.stderr
