#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
# SPDX-License-Identifier: MIT
"""cli_everything_prebuild.py — prebuild gate for CLI entrypoints.

Defect class: cli_everything_prebuild
For each entrypoint that exists, `python -I` runs `--help` and every
discovered subcommand's `--help`. Exit 0 is required.

Entrypoints:
  python -m paper_mcp          when paper_mcp/__main__.py exists
  python -m sovereign          when sovereign/__main__.py exists
  scripts/sovereign_cli.py     when that file exists

python -I on 3.11+ does not put the repository on sys.path (it implies -P).
This gate never passes -P. The isolated child inserts the repository root
itself, which is valid on 3.10 and later.

When none of the entrypoints exist the process exits 0 and prints one JSON
line: {"skipped": "skipped: paper_mcp/ absent", ...}.

Exit: 0 clean, 1 a help command failed, 2 usage/IO or an incomplete scan
(the entrypoint could not be started at all, unless listed in
--known-unparsed).
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

CATALOGUED_CLASS = "cli_everything_prebuild"
REPO = Path(__file__).resolve().parents[1]
_BRACE = re.compile(r"\{([^{}\n]+)\}")


class Reason:
    START = "start_error"


class Kind:
    HELP = "help_failed"


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
    commands: List[str] = field(default_factory=list)

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
            "commands": list(self.commands),
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


def entrypoints(root: Path) -> List[Tuple[str, str, Path]]:
    """Return (kind, name, path) for entrypoints that exist under root."""
    found = []
    paper = root / "paper_mcp" / "__main__.py"
    if paper.is_file():
        found.append(("module", "paper_mcp", paper))
    sovereign = root / "sovereign" / "__main__.py"
    if sovereign.is_file():
        found.append(("module", "sovereign", sovereign))
    script = root / "scripts" / "sovereign_cli.py"
    if script.is_file():
        found.append(("script", "sovereign_cli", script))
    return found


def _isolated(root: Path, kind: str, name: str, path: Path, args: Sequence[str]) -> subprocess.CompletedProcess:
    """Run an entrypoint under python -I. Never passes -P."""
    if kind == "module":
        code = (
            "import sys\n"
            "from runpy import run_module\n"
            "sys.path.insert(0, sys.argv[1])\n"
            "mod = sys.argv[2]\n"
            "sys.argv = [mod] + sys.argv[3:]\n"
            "run_module(mod, run_name='__main__', alter_sys=True)\n"
        )
        cmd = [sys.executable, "-I", "-c", code, str(root), name, *args]
    else:
        cmd = [sys.executable, "-I", str(path), *args]
    return subprocess.run(
        cmd,
        cwd=str(root),
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )


def subcommands_from_help(text: str) -> List[str]:
    match = _BRACE.search(text)
    if not match:
        return []
    return [part.strip() for part in match.group(1).split(",") if part.strip()]


def _record(metrics: Metrics, path: Path, reason: str, detail: str, known_map: Dict[str, str]) -> None:
    metrics.unparsed += 1
    known = str(path.resolve()) in known_map
    if known:
        metrics.known_unparsed += 1
    metrics.parse_failures.append(ParseFailure(str(path), reason, detail, known))


def _note(findings: List[Finding], path: str, detail: str) -> None:
    findings.append(Finding(path, Kind.HELP, detail))


def scan(root: Path, known_unparsed: Optional[Dict[str, str]] = None) -> Tuple[List[Finding], Metrics, bool]:
    known_unparsed = known_unparsed or {}
    targets = entrypoints(root)
    if not targets:
        return [], Metrics(), True
    findings: List[Finding] = []
    metrics = Metrics()
    for kind, name, path in targets:
        metrics.files_seen += 1
        label = "{0} --help".format(name)
        try:
            top = _isolated(root, kind, name, path, ["--help"])
        except (OSError, subprocess.TimeoutExpired) as exc:
            _record(metrics, path, Reason.START, "{0}: {1}".format(label, exc), known_unparsed)
            continue
        if top.returncode != 0:
            _record(
                metrics,
                path,
                Reason.START,
                "{0} exited {1}: {2}".format(label, top.returncode, (top.stderr or top.stdout).strip()),
                known_unparsed,
            )
            continue
        metrics.parsed += 1
        metrics.commands.append(label)
        for sub in subcommands_from_help(top.stdout + "\n" + top.stderr):
            sub_label = "{0} {1} --help".format(name, sub)
            try:
                proc = _isolated(root, kind, name, path, [sub, "--help"])
            except (OSError, subprocess.TimeoutExpired) as exc:
                _note(findings, str(path), "{0}: {1}".format(sub_label, exc))
                continue
            metrics.commands.append(sub_label)
            if proc.returncode != 0:
                detail = (proc.stderr or proc.stdout or "").strip()
                _note(findings, str(path), "{0} exited {1}: {2}".format(sub_label, proc.returncode, detail))
    metrics.findings = len(findings)
    for item in findings:
        metrics.by_kind[item.kind] = metrics.by_kind.get(item.kind, 0) + 1
    return findings, metrics, False


def render(findings: List[Finding], metrics: Metrics) -> str:
    lines = [
        "cli_everything_prebuild -- {0} scan".format(CATALOGUED_CLASS),
        "files_seen: {0}".format(metrics.files_seen),
        "parsed    : {0}".format(metrics.parsed),
        "unparsed  : {0} (known: {1}, blocking: {2})".format(
            metrics.unparsed, metrics.known_unparsed, metrics.blocking_unparsed
        ),
        "findings  : {0}".format(metrics.findings),
        "commands  : {0}".format(", ".join(metrics.commands) or "(none)"),
        "=" * 64,
    ]
    for pf in metrics.parse_failures:
        tag = "KNOWN-UNPARSED" if pf.known else "UNPARSED"
        lines.append("  {0} {1}: {2}: {3}".format(tag, pf.path, pf.reason, pf.detail))
    if not findings and not metrics.parse_failures:
        lines.append("cli prebuild clean")
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
    parts = [
        "cli_everything_prebuild: INCOMPLETE SCAN -- {0} of {1} "
        "entrypoints could not be started; refusing to report a pass.".format(
            len(blocking), metrics.files_seen
        )
    ]
    for pf in blocking[:5]:
        parts.append("  {0}: {1}: {2}".format(pf.path, pf.reason, pf.detail))
    return "\n".join(parts)


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Prebuild gate for CLI --help surfaces.")
    ap.add_argument("root", nargs="?", type=Path, default=REPO, help="repository root to scan")
    ap.add_argument("--json", action="store_true", help="emit the scan as JSON")
    ap.add_argument(
        "--known-unparsed",
        type=Path,
        default=None,
        metavar="LIST",
        help=(
            "file listing entrypoints already known not to start (one "
            "repo-relative path per line, '# note' allowed). Listed start "
            "failures are reported as KNOWN-UNPARSED instead of forcing exit 2."
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
