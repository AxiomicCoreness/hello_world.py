#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
assert_no_port_binding.py — single-file AST check.

Certifies exactly this: the given source file contains no
  - assignment to a port-named variable
  - call to a socket bind method (bind, create_server, ...)
  - call to a server constructor with a port literal in its arguments

It does NOT certify that the service has no assigned port. Ports can
also arrive from:
  - uvicorn CLI flags (--port)
  - UVICORN_PORT / PORT environment variables
  - Dockerfile EXPOSE
  - docker-compose `ports:`
  - systemd / process-manager config
Those layers are outside this file's reach.

Exit codes:
  0  no port assignment or bind call found in the file
  1  at least one was found
  2  source file missing or unparseable

The claim is narrow on purpose. If you need the wider claim ("this
service binds no port anywhere"), the check must be extended to the
deployment surfaces listed above, each parsed as a document.
"""
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

SOURCE = Path("port380_mcp.py")

# Port variable names by word boundary. Matches PORT, UVICORN_PORT,
# BIND_PORT, MY_PORT. Rejects REPORT, AIRPORT, PORTFOLIO, SUPPORT.
PORT_NAME = re.compile(r"^(?:[A-Z][A-Z0-9_]*)?PORT(?:_[A-Z0-9_]+)?$")

# Socket-bind method names.
BIND_METHODS = {"bind", "create_server"}

# Server constructors whose positional or keyword arguments can carry a port.
SERVER_CTORS = {
    "HTTPServer",
    "ThreadingHTTPServer",
    "TCPServer",
    "ThreadingTCPServer",
    "UDPServer",
    "create_server",  # socket.create_server
    "run",            # uvicorn.run
}

# Ports are integers in [1, 65535].
PORT_MIN = 1
PORT_MAX = 65535


def is_port_variable(name: str) -> bool:
    return bool(PORT_NAME.fullmatch(name.upper()))


def dotted_name(node: ast.AST) -> str:
    """Human-readable dotted name of a Name/Attribute chain, or ''."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = dotted_name(node.value)
        return f"{base}.{node.attr}" if base else node.attr
    return ""


def contains_port_literal(node: ast.AST) -> tuple[bool, int | None]:
    """True if node is an int in the port range, or a tuple containing one."""
    if isinstance(node, ast.Constant) and isinstance(node.value, int):
        if PORT_MIN <= node.value <= PORT_MAX:
            return True, node.value
    if isinstance(node, ast.Tuple):
        for elt in node.elts:
            hit, val = contains_port_literal(elt)
            if hit:
                return True, val
    return False, None


def find_violations(tree: ast.AST) -> list[str]:
    findings: list[str] = []

    for node in ast.walk(tree):
        # 1. Assignment to a port-named variable.
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and is_port_variable(t.id):
                    findings.append(
                        f"line {node.lineno}: assignment to port-named "
                        f"variable {t.id!r}"
                    )
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if is_port_variable(node.target.id):
                findings.append(
                    f"line {node.lineno}: annotated assignment to port-named "
                    f"variable {node.target.id!r}"
                )

        # 2. Call checks.
        if not isinstance(node, ast.Call):
            continue

        full = dotted_name(node.func)
        leaf = full.rsplit(".", 1)[-1] if full else ""

        # 2a. Bind methods.
        if leaf in BIND_METHODS:
            findings.append(f"line {node.lineno}: call to {full or leaf}()")

        # 2b. Server constructors with a port literal.
        if leaf in SERVER_CTORS:
            # Keyword arguments
            for kw in node.keywords:
                if kw.arg in ("port", "bind_port"):
                    findings.append(
                        f"line {node.lineno}: {full or leaf}(... "
                        f"{kw.arg}={ast.unparse(kw.value)})"
                    )
            # Positional arguments
            for i, arg in enumerate(node.args):
                hit, val = contains_port_literal(arg)
                if hit:
                    findings.append(
                        f"line {node.lineno}: {full or leaf}(...) "
                        f"positional arg {i} contains port {val}"
                    )
                    break

    return findings


def main() -> int:
    if not SOURCE.exists():
        print(f"::error::{SOURCE} not found", file=sys.stderr)
        return 2

    try:
        tree = ast.parse(SOURCE.read_text())
    except SyntaxError as e:
        print(f"::error::{SOURCE} failed to parse: {e}", file=sys.stderr)
        return 2

    findings = find_violations(tree)

    if findings:
        for f in findings:
            print(f"FAIL: {f}")
        return 1

    print(f"OK: {SOURCE} contains no port assignment or bind call")
    print("NOTE: this certifies only the file. Deployment surfaces "
          "(Dockerfile, compose, CLI, env) are not checked.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
