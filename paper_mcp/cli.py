# SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
# SPDX-License-Identifier: MIT
"""Command line for paper_mcp. Every subcommand uses CanvasStore."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, List, Optional, Sequence, TextIO

from .server import (
    DEFAULT_HTTP_PORT,
    CanvasError,
    CanvasStore,
    make_http_server,
    serve_stdio,
)


def _hoist_globals(argv: Sequence[str]) -> List[str]:
    """Accept ``--root`` and ``--json`` before or after the subcommand."""
    hoisted: List[str] = []
    rest: List[str] = []
    i = 0
    items = list(argv)
    while i < len(items):
        arg = items[i]
        if arg == "--json":
            hoisted.append(arg)
        elif arg == "--root":
            if i + 1 >= len(items):
                hoisted.append(arg)
            else:
                hoisted.extend([arg, items[i + 1]])
                i += 1
        elif arg.startswith("--root="):
            hoisted.append(arg)
        else:
            rest.append(arg)
        i += 1
    return hoisted + rest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="paper_mcp",
        description="Filesystem design canvases (MCP stdio, HTTP, and a local CLI).",
    )
    parser.add_argument(
        "--root",
        default=None,
        help="Canvas directory (overrides PAPER_MCP_ROOT).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON on stdout.",
    )
    sub = parser.add_subparsers(dest="command")
    sub.required = False

    sub.add_parser("serve", help="Speak MCP JSON-RPC on stdio (default).")

    http = sub.add_parser(
        "serve-http",
        help="JSON-RPC POST /mcp and GET /healthz on loopback.",
    )
    http.add_argument("--bind", default=None, help="Bind host. Only 127.0.0.1.")
    http.add_argument("--port", type=int, default=DEFAULT_HTTP_PORT)
    http.add_argument(
        "--cors-origin",
        default=None,
        help="Reflect the request Origin, or '*' to send a wildcard.",
    )

    sub.add_parser("list", help="List canvas names.")
    sub.add_parser("resources", help="List canvas resource URIs.")

    read = sub.add_parser("read", help="Print one canvas.")
    read.add_argument("name")

    write = sub.add_parser("write", help="Write a canvas from --file or stdin.")
    write.add_argument("name")
    write.add_argument("--file", default=None, help="Read content from PATH.")

    patch = sub.add_parser("patch", help="Replace find with replace in a canvas.")
    patch.add_argument("name")
    patch.add_argument("--find", required=True)
    patch.add_argument("--replace", required=True)

    delete = sub.add_parser("delete", help="Delete a canvas.")
    delete.add_argument("name")
    return parser


def _emit(payload: Any, as_json: bool, stream: TextIO) -> None:
    if as_json:
        stream.write(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        stream.write("\n")
    elif isinstance(payload, str):
        stream.write(payload)
        if not payload.endswith("\n"):
            stream.write("\n")
    else:
        stream.write(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        stream.write("\n")


def _fail(message: str, as_json: bool) -> int:
    if as_json:
        sys.stderr.write(json.dumps({"ok": False, "error": message}) + "\n")
    else:
        sys.stderr.write("paper_mcp: {0}\n".format(message))
    return 1


def _read_write_content(file_arg: Optional[str]) -> str:
    if file_arg:
        return Path(file_arg).read_text(encoding="utf-8")
    if sys.stdin.isatty():
        raise CanvasError("write: pass --file PATH or pipe content on stdin")
    return sys.stdin.read()


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    if argv is None:
        argv = sys.argv[1:]
    args = parser.parse_args(_hoist_globals(argv))
    command = args.command or "serve"
    try:
        store = CanvasStore.from_env(args.root)
    except (CanvasError, ValueError) as exc:
        return _fail(str(exc), args.json)

    try:
        if command == "serve":
            serve_stdio(store)
            return 0
        if command == "serve-http":
            server = make_http_server(
                store,
                host=args.bind,
                port=args.port,
                cors_origin=args.cors_origin,
            )
            host, port = server.server_address[:2]
            sys.stdout.write(
                "paper_mcp http listening on {0} {1}\n".format(host, port)
            )
            sys.stdout.flush()
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                pass
            finally:
                server.server_close()
            return 0
        if command == "list":
            names = store.list_canvases()
            if args.json:
                _emit({"ok": True, "canvases": names}, True, sys.stdout)
            else:
                for name in names:
                    sys.stdout.write(name + "\n")
            return 0
        if command == "resources":
            items = store.resources()
            if args.json:
                _emit({"ok": True, "resources": items}, True, sys.stdout)
            else:
                for item in items:
                    sys.stdout.write(
                        "{0}\t{1}\n".format(item["uri"], item["mimeType"])
                    )
            return 0
        if command == "read":
            text = store.read(args.name)
            if args.json:
                _emit(
                    {
                        "ok": True,
                        "name": args.name,
                        "content": text,
                        "mimeType": _mime_for(args.name),
                    },
                    True,
                    sys.stdout,
                )
            else:
                sys.stdout.write(text)
                if not text.endswith("\n"):
                    sys.stdout.write("\n")
            return 0
        if command == "write":
            content = _read_write_content(args.file)
            result = store.write(args.name, content)
            result["ok"] = True
            _emit(result if args.json else "wrote {0}".format(args.name), args.json, sys.stdout)
            return 0
        if command == "patch":
            result = store.patch(args.name, args.find, args.replace)
            result["ok"] = True
            if args.json:
                _emit(result, True, sys.stdout)
            else:
                _emit(
                    "patched {0} ({1})".format(args.name, result["replacements"]),
                    False,
                    sys.stdout,
                )
            return 0
        if command == "delete":
            result = store.delete(args.name)
            result["ok"] = True
            _emit(result if args.json else "deleted {0}".format(args.name), args.json, sys.stdout)
            return 0
    except CanvasError as exc:
        return _fail(str(exc), args.json)
    except OSError as exc:
        return _fail(str(exc), args.json)
    except SystemExit as exc:
        code = exc.code
        if isinstance(code, str):
            sys.stderr.write(code + "\n")
            return 1
        if code is None:
            return 0
        return int(code)
    parser.error("unknown command")
    return 2


def _mime_for(name: str) -> str:
    from .server import _mime

    return _mime(name)
