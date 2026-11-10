#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
# SPDX-License-Identifier: MIT
"""paper_mcp_prebuild.py — prebuild gate for the filesystem canvas package.

Defect class: paper_mcp_prebuild
Checks, one walk:
  compile_error       a module does not compile under python -I
  missing_required    a required package file is absent
  tool_cli_mismatch   MCP tool names do not match CLI subcommands
  path_sanitization   names with '..', separators, or absolute paths pass
  bind                default bind is not loopback, or 0.0.0.0/::/* is accepted

Pure stdlib. Bytecode is written to a temp cfile, never next to the source.
Exit: 0 clean, 1 findings, 2 usage/IO or incomplete scan.

Incomplete scan: a module that cannot be compiled, or a required file that
is missing, exits 2 instead of reporting a pass. Compile failures may be
listed in --known-unparsed; a missing required file never can.

When paper_mcp/ and tools/paper-mcp/ are both absent the process exits 0
and prints one JSON line: {"skipped": "skipped: paper_mcp/ absent", ...}.
"""

from __future__ import annotations

import argparse
import importlib
import json
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

CATALOGUED_CLASS = "paper_mcp_prebuild"
REPO = Path(__file__).resolve().parents[1]
REQUIRED = ("__init__.py", "__main__.py", "server.py", "cli.py", "README.md")
TRANSPORT = frozenset(("serve", "serve-http", "resources"))
REFUSED_BINDS = ("0.0.0.0", "::", "[::]", "*")


class Reason:
    COMPILE = "compile_error"
    MISSING = "missing_required"
    READ = "read_error"


class Kind:
    TOOLS = "tool_cli_mismatch"
    PATH = "path_sanitization"
    BIND = "bind"


@dataclass
class Finding:
    path: str
    kind: str
    detail: str


@dataclass
class ParseFailure:
    path: str
    reason: str
    detail: str
    known: bool = False


@dataclass
class Metrics:
    files_seen: int = 0
    parsed: int = 0
    unparsed: int = 0
    known_unparsed: int = 0
    findings: int = 0
    by_kind: dict = field(default_factory=dict)
    parse_failures: List[ParseFailure] = field(default_factory=list)

    @property
    def blocking_unparsed(self) -> int:
        return self.unparsed - self.known_unparsed

    def as_dict(self) -> dict:
        return {
            "files_seen": self.files_seen,
            "parsed": self.parsed,
            "unparsed": self.unparsed,
            "known_unparsed": self.known_unparsed,
            "blocking_unparsed": self.blocking_unparsed,
            "findings": self.findings,
            "by_kind": self.by_kind,
        }


def load_known_unparsed(list_file: Path) -> Dict[str, str]:
    """One path per line, optional '# note'. Resolved against scripts/.."""
    base = list_file.resolve().parent.parent
    known: Dict[str, str] = {}
    for raw in list_file.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        rel, _, note = line.partition("#")
        rel = rel.strip()
        known[str((base / rel).resolve())] = note.strip()
    return known


def _py_files(directory: Path) -> List[Path]:
    found = []
    for path in sorted(directory.rglob("*.py")):
        if not path.is_file():
            continue
        if "__pycache__" in path.parts:
            continue
        found.append(path)
    return found


def compile_isolated(path: Path, dest: Path) -> Tuple[bool, str]:
    """Compile with python -I into dest. Does not write __pycache__."""
    proc = subprocess.run(
        [
            sys.executable,
            "-I",
            "-c",
            "import py_compile, sys\n"
            "py_compile.compile(sys.argv[1], cfile=sys.argv[2], doraise=True)\n",
            str(path),
            str(dest),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    detail = (proc.stderr or proc.stdout or "").strip()
    return proc.returncode == 0, detail


def _record_failure(metrics: Metrics, path: Path, reason: str, detail: str, known_map: Dict[str, str]) -> None:
    metrics.unparsed += 1
    excusable = reason == Reason.COMPILE
    known = excusable and str(path.resolve()) in known_map
    if known:
        metrics.known_unparsed += 1
    metrics.parse_failures.append(ParseFailure(str(path), reason, detail, known))


def _note(findings: List[Finding], path: str, kind: str, detail: str) -> None:
    findings.append(Finding(path, kind, detail))


def _command_names(cli_mod) -> List[str]:
    import argparse

    parser = cli_mod.build_parser()
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            return list(action.choices)
    return []


def _tool_names(server_mod) -> List[str]:
    schemas = server_mod._tool_schemas()
    return [item["name"] for item in schemas]


def _self_check(root: Path, findings: List[Finding]) -> Optional[str]:
    """Return an error string when the package cannot be imported."""
    saved_path = list(sys.path)
    saved = {}
    for key in list(sys.modules):
        if key == "paper_mcp" or key.startswith("paper_mcp."):
            saved[key] = sys.modules.pop(key)
    sys.path.insert(0, str(root))
    try:
        server = importlib.import_module("paper_mcp.server")
        cli = importlib.import_module("paper_mcp.cli")
        tools = _tool_names(server)
        commands = _command_names(cli)
        tool_cmds = set()
        for name in tools:
            tool_cmds.add(name[len("canvas_"):] if name.startswith("canvas_") else name)
        data_commands = set(commands) - set(TRANSPORT)
        if tool_cmds != data_commands or not tool_cmds.issubset(set(commands)):
            _note(
                findings,
                str(root / "paper_mcp"),
                Kind.TOOLS,
                "tools {0} vs commands {1} (transport {2})".format(
                    sorted(tool_cmds), sorted(data_commands), sorted(TRANSPORT)
                ),
            )
        store = server.CanvasStore(root / ".paper_mcp_prebuild_unused")
        for bad in ("../secret.html", "/etc/passwd", "sub/x.html", "..", ""):
            try:
                store.validate_name(bad)
            except server.CanvasError:
                continue
            _note(
                findings,
                str(root / "paper_mcp" / "server.py"),
                Kind.PATH,
                "accepted unsafe name {0!r}".format(bad),
            )
        try:
            store.validate_name("board.html")
        except server.CanvasError as exc:
            _note(findings, str(root / "paper_mcp" / "server.py"), Kind.PATH, str(exc))
        if getattr(server, "DEFAULT_BIND", None) != "127.0.0.1":
            _note(
                findings,
                str(root / "paper_mcp" / "server.py"),
                Kind.BIND,
                "DEFAULT_BIND is {0!r}".format(getattr(server, "DEFAULT_BIND", None)),
            )
        try:
            bound = server.resolve_loopback_host(None)
        except SystemExit as exc:
            _note(findings, str(root / "paper_mcp" / "server.py"), Kind.BIND, "default bind refused: {0}".format(exc))
        else:
            if bound != "127.0.0.1":
                _note(findings, str(root / "paper_mcp" / "server.py"), Kind.BIND, "default resolved to {0}".format(bound))
        for host in REFUSED_BINDS:
            try:
                server.resolve_loopback_host(host)
            except SystemExit:
                continue
            _note(
                findings,
                str(root / "paper_mcp" / "server.py"),
                Kind.BIND,
                "accepted bind {0!r}".format(host),
            )
        return None
    except Exception as exc:
        return "{0}: {1}".format(type(exc).__name__, exc)
    finally:
        for key in list(sys.modules):
            if key == "paper_mcp" or key.startswith("paper_mcp."):
                sys.modules.pop(key, None)
        sys.modules.update(saved)
        sys.path[:] = saved_path


def scan(root: Path, known_unparsed: Optional[Dict[str, str]] = None) -> Tuple[List[Finding], Metrics, bool]:
    """Return findings, metrics, and whether every target directory was absent."""
    known_unparsed = known_unparsed or {}
    package = root / "paper_mcp"
    extra = root / "tools" / "paper-mcp"
    if not package.is_dir() and not extra.is_dir():
        return [], Metrics(), True

    findings: List[Finding] = []
    metrics = Metrics()
    compile_targets: List[Path] = []
    if package.is_dir():
        for name in REQUIRED:
            path = package / name
            metrics.files_seen += 1
            if not path.is_file():
                _record_failure(metrics, path, Reason.MISSING, "required file absent", known_unparsed)
            elif name.endswith(".py"):
                compile_targets.append(path)
            else:
                metrics.parsed += 1
        for path in _py_files(package):
            if path not in compile_targets:
                metrics.files_seen += 1
                compile_targets.append(path)
    if extra.is_dir():
        extras = _py_files(extra)
        if not extras:
            metrics.files_seen += 1
            metrics.parsed += 1
        for path in extras:
            metrics.files_seen += 1
            compile_targets.append(path)

    with tempfile.TemporaryDirectory(prefix="paper-mcp-prebuild-") as tmp:
        for index, path in enumerate(compile_targets):
            dest = Path(tmp) / "mod{0}.pyc".format(index)
            ok, detail = compile_isolated(path, dest)
            if ok:
                metrics.parsed += 1
            else:
                _record_failure(metrics, path, Reason.COMPILE, detail or "compile failed", known_unparsed)

    if package.is_dir() and metrics.blocking_unparsed == 0:
        imported = _self_check(root, findings)
        if imported:
            _record_failure(
                metrics,
                package / "server.py",
                Reason.READ,
                imported,
                known_unparsed,
            )
    metrics.findings = len(findings)
    for item in findings:
        metrics.by_kind[item.kind] = metrics.by_kind.get(item.kind, 0) + 1
    return findings, metrics, False


def render(findings: List[Finding], metrics: Metrics) -> str:
    lines = [
        "paper_mcp_prebuild -- {0} scan".format(CATALOGUED_CLASS),
        "files_seen: {0}".format(metrics.files_seen),
        "parsed    : {0}".format(metrics.parsed),
        "unparsed  : {0} (known: {1}, blocking: {2})".format(
            metrics.unparsed, metrics.known_unparsed, metrics.blocking_unparsed
        ),
        "findings  : {0}".format(metrics.findings),
        "by_kind   : {0}".format(json.dumps(metrics.by_kind, sort_keys=True)),
        "=" * 64,
    ]
    for pf in metrics.parse_failures:
        tag = "KNOWN-UNPARSED" if pf.known else "UNPARSED"
        lines.append("  {0} {1}: {2}: {3}".format(tag, pf.path, pf.reason, pf.detail))
    if not findings and not metrics.parse_failures:
        lines.append("paper_mcp prebuild clean")
        return "\n".join(lines)
    for item in findings:
        lines.append("")
        lines.append("  {0}".format(item.path))
        lines.append("    class  : {0}/{1}".format(CATALOGUED_CLASS, item.kind))
        lines.append("    detail : {0}".format(item.detail))
    return "\n".join(lines)


def summary(findings: List[Finding], metrics: Metrics, known_list: Optional[Path]) -> dict:
    return {
        "class": CATALOGUED_CLASS,
        "metrics": metrics.as_dict(),
        "known_unparsed_list": str(known_list) if known_list else None,
        "parse_failures": [
            {"path": pf.path, "reason": pf.reason, "detail": pf.detail, "known": pf.known}
            for pf in metrics.parse_failures
        ],
        "findings": [
            {"path": item.path, "kind": item.kind, "detail": item.detail} for item in findings
        ],
    }


def incomplete_message(metrics: Metrics) -> str:
    blocking = [pf for pf in metrics.parse_failures if not pf.known]
    by_reason: Dict[str, int] = {}
    for pf in blocking:
        by_reason[pf.reason] = by_reason.get(pf.reason, 0) + 1
    parts = [
        "paper_mcp_prebuild: INCOMPLETE SCAN -- {0} of {1} "
        "could not be checked ({2}); refusing to report a pass.".format(
            len(blocking),
            metrics.files_seen,
            json.dumps(by_reason, sort_keys=True),
        )
    ]
    for pf in blocking[:5]:
        parts.append("  {0}: {1}: {2}".format(pf.path, pf.reason, pf.detail))
    if len(blocking) > 5:
        parts.append("  ... and {0} more (see --json parse_failures)".format(len(blocking) - 5))
    return "\n".join(parts)


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Prebuild gate for paper_mcp canvases.")
    ap.add_argument("root", nargs="?", type=Path, default=REPO, help="repository root to scan")
    ap.add_argument("--json", action="store_true", help="emit the scan as JSON")
    ap.add_argument(
        "--known-unparsed",
        type=Path,
        default=None,
        metavar="LIST",
        help=(
            "file listing modules already known not to compile (one repo-relative "
            "path per line, '# note' allowed). Listed compile errors are reported "
            "as KNOWN-UNPARSED instead of forcing exit 2. Never excuses a missing "
            "required file."
        ),
    )
    args = ap.parse_args(argv)
    if not args.root.exists():
        print("not found: {0}".format(args.root), file=sys.stderr)
        return 2
    known: Dict[str, str] = {}
    if args.known_unparsed is not None:
        if not args.known_unparsed.is_file():
            print("known-unparsed list not found: {0}".format(args.known_unparsed), file=sys.stderr)
            return 2
        known = load_known_unparsed(args.known_unparsed)
    findings, metrics, skipped = scan(args.root, known)
    if skipped:
        print(json.dumps({"class": CATALOGUED_CLASS, "skipped": "skipped: paper_mcp/ absent"}))
        return 0
    if args.json:
        print(json.dumps(summary(findings, metrics, args.known_unparsed), indent=2))
    else:
        print(render(findings, metrics))
    if metrics.blocking_unparsed:
        print(incomplete_message(metrics), file=sys.stderr)
        return 2
    return 0 if not findings else 1


if __name__ == "__main__":
    raise SystemExit(main())
