#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
# SPDX-License-Identifier: MIT
"""cors_anywhere_prebuild.py — prebuild gate for loopback CORS.

Defect class: cors_anywhere_prebuild
Checks:
  layout          tools/cors-anywhere/ is missing an expected file
  bind            0.0.0.0, ::, [::], or * is not refused, or the listen
                  address is not 127.0.0.1
  preflight       OPTIONS handling is absent
  vary            Vary: Origin is absent
  healthz         /healthz is absent
  parse_error     package.json is not JSON, or a file cannot be read

Pure stdlib. Scans tools/cors-anywhere/ when that directory exists, and the
paper_mcp HTTP handler when paper_mcp/server.py exists. Either target may
be absent. When both are absent the process exits 0 and prints one JSON
line: {"skipped": "skipped: tools/cors-anywhere/ absent", ...}.

Exit: 0 clean, 1 findings, 2 usage/IO or incomplete scan.
A listed --known-unparsed path may fail to read or parse. A missing
loopback refusal is never excused.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

CATALOGUED_CLASS = "cors_anywhere_prebuild"
REPO = Path(__file__).resolve().parents[1]
CORS_FILES = ("server.js", "package.json", "README.md", "help.txt")
REFUSED = ("0.0.0.0", "::", "[::]", "*")


class Reason:
    READ = "read_error"
    PARSE = "parse_error"
    MISSING = "missing_required"


class Kind:
    LAYOUT = "layout"
    BIND = "bind"
    PREFLIGHT = "preflight"
    VARY = "vary"
    HEALTHZ = "healthz"


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


def _record(metrics: Metrics, path: Path, reason: str, detail: str, known_map: Dict[str, str]) -> None:
    metrics.unparsed += 1
    excusable = reason in (Reason.READ, Reason.PARSE)
    known = excusable and str(path.resolve()) in known_map
    if known:
        metrics.known_unparsed += 1
    metrics.parse_failures.append(ParseFailure(str(path), reason, detail, known))


def _note(findings: List[Finding], path: str, kind: str, detail: str) -> None:
    findings.append(Finding(path, kind, detail))


def _read(path: Path, metrics: Metrics, known_map: Dict[str, str]) -> Optional[str]:
    metrics.files_seen += 1
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        _record(metrics, path, Reason.READ, str(exc), known_map)
        return None
    metrics.parsed += 1
    return text


def _has_star(text: str) -> bool:
    return "'*'" in text or '"*"' in text


def _bind_tokens(text: str) -> List[str]:
    missing = []
    for token in ("0.0.0.0", "::", "[::]", "127.0.0.1"):
        if token not in text:
            missing.append(token)
    if not _has_star(text):
        missing.append("*")
    return missing


def _scan_cors_dir(directory: Path, findings: List[Finding], metrics: Metrics, known_map: Dict[str, str]) -> None:
    present = {}
    for name in CORS_FILES:
        path = directory / name
        if not path.is_file():
            metrics.files_seen += 1
            metrics.parsed += 1
            _note(findings, str(path), Kind.LAYOUT, "expected file absent")
            continue
        text = _read(path, metrics, known_map)
        if text is None:
            continue
        present[name] = text
    package = present.get("package.json")
    if package is not None:
        try:
            json.loads(package)
        except json.JSONDecodeError as exc:
            metrics.parsed -= 1
            _record(metrics, directory / "package.json", Reason.PARSE, str(exc), known_map)
    server = present.get("server.js")
    if server is None:
        return
    missing = _bind_tokens(server)
    if missing or "127.0.0.1" not in server:
        _note(
            findings,
            str(directory / "server.js"),
            Kind.BIND,
            "loopback refusal missing tokens: {0}".format(", ".join(missing) or "127.0.0.1"),
        )


def _scan_paper_http(root: Path, findings: List[Finding], metrics: Metrics, known_map: Dict[str, str]) -> None:
    path = root / "paper_mcp" / "server.py"
    text = _read(path, metrics, known_map)
    if text is None:
        return
    missing = _bind_tokens(text)
    if missing:
        _note(findings, str(path), Kind.BIND, "loopback refusal missing tokens: {0}".format(", ".join(missing)))
    if "def do_OPTIONS" not in text:
        _note(findings, str(path), Kind.PREFLIGHT, "OPTIONS preflight handler is absent")
    if '"Vary"' not in text or '"Origin"' not in text:
        _note(findings, str(path), Kind.VARY, "Vary: Origin is absent")
    if '"/healthz"' not in text:
        _note(findings, str(path), Kind.HEALTHZ, "/healthz is absent")
    saved_path = list(sys.path)
    saved = {}
    for key in list(sys.modules):
        if key == "paper_mcp" or key.startswith("paper_mcp."):
            saved[key] = sys.modules.pop(key)
    sys.path.insert(0, str(root))
    try:
        server = importlib.import_module("paper_mcp.server")
        resolve = getattr(server, "resolve_loopback_host", None)
        if resolve is None:
            _note(findings, str(path), Kind.BIND, "resolve_loopback_host is absent")
        else:
            if getattr(server, "DEFAULT_BIND", None) != "127.0.0.1":
                _note(findings, str(path), Kind.BIND, "DEFAULT_BIND is not 127.0.0.1")
            try:
                if resolve(None) != "127.0.0.1":
                    _note(findings, str(path), Kind.BIND, "default bind is not 127.0.0.1")
            except SystemExit:
                _note(findings, str(path), Kind.BIND, "default bind was refused")
            for host in REFUSED:
                try:
                    resolve(host)
                except SystemExit:
                    continue
                _note(findings, str(path), Kind.BIND, "accepted bind {0!r}".format(host))
    except Exception as exc:
        metrics.parsed -= 1
        _record(metrics, path, Reason.READ, "{0}: {1}".format(type(exc).__name__, exc), known_map)
    finally:
        for key in list(sys.modules):
            if key == "paper_mcp" or key.startswith("paper_mcp."):
                sys.modules.pop(key, None)
        sys.modules.update(saved)
        sys.path[:] = saved_path


def scan(root: Path, known_unparsed: Optional[Dict[str, str]] = None) -> Tuple[List[Finding], Metrics, bool]:
    known_unparsed = known_unparsed or {}
    cors = root / "tools" / "cors-anywhere"
    http = root / "paper_mcp" / "server.py"
    if not cors.is_dir() and not http.is_file():
        return [], Metrics(), True
    findings: List[Finding] = []
    metrics = Metrics()
    if cors.is_dir():
        _scan_cors_dir(cors, findings, metrics, known_unparsed)
    if http.is_file():
        _scan_paper_http(root, findings, metrics, known_unparsed)
    metrics.findings = len(findings)
    for item in findings:
        metrics.by_kind[item.kind] = metrics.by_kind.get(item.kind, 0) + 1
    return findings, metrics, False


def render(findings: List[Finding], metrics: Metrics) -> str:
    lines = [
        "cors_anywhere_prebuild -- {0} scan".format(CATALOGUED_CLASS),
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
        lines.append("cors prebuild clean")
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
        "cors_anywhere_prebuild: INCOMPLETE SCAN -- {0} of {1} "
        "could not be checked ({2}); refusing to report a pass.".format(
            len(blocking),
            metrics.files_seen,
            json.dumps(by_reason, sort_keys=True),
        )
    ]
    for pf in blocking[:5]:
        parts.append("  {0}: {1}: {2}".format(pf.path, pf.reason, pf.detail))
    return "\n".join(parts)


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Prebuild gate for loopback CORS.")
    ap.add_argument("root", nargs="?", type=Path, default=REPO, help="repository root to scan")
    ap.add_argument("--json", action="store_true", help="emit the scan as JSON")
    ap.add_argument(
        "--known-unparsed",
        type=Path,
        default=None,
        metavar="LIST",
        help=(
            "file listing paths already known not to parse (one repo-relative "
            "path per line, '# note' allowed). Listed read/parse errors are "
            "reported as KNOWN-UNPARSED instead of forcing exit 2."
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
        print(json.dumps({"class": CATALOGUED_CLASS, "skipped": "skipped: tools/cors-anywhere/ absent"}))
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
