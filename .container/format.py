#!/usr/bin/env python3
"""
format.py — Clarke Yoursa Tee
One-line purpose: AST header formatter and validator for .container artifacts.
Rules: A1-A5, C1-C2.
Seal: SHA3-256("GARDEN.ASTGUARD.v1" || 0x00 || canonical_json({domain, content}))
digest: NOT_COMPUTED
"""
from __future__ import annotations

import ast
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

DOMAIN = "GARDEN.ASTGUARD.v1"
SEP = b"\x00"
REQUIRED_FIELDS = ("filename", "author", "purpose", "rules", "seal", "digest")
CONTRACT_VERSION = "v1.0.0"
SCHEMA = "draft-07"
AST_HEADER_VERSION = "1.0.0"

LEGEND: Dict[str, str] = {
    "north star": "NORTH_STAR_HZ   = 71.975",
    "phase lock": "PHASE_LOCK_DEG  = 202.6",
    "compass":    "not in thread",
}


def read_source(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def docstring_node(source: str):
    tree = ast.parse(source)
    if not tree.body:
        return None
    node = tree.body[0]
    if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
        return node
    return None


def docstring_text(source: str) -> str:
    node = docstring_node(source)
    return "" if node is None else node.value.value


def docstring_line(source: str) -> int:
    node = docstring_node(source)
    return -1 if node is None else node.lineno


def parse_header(docstring: str) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for raw in docstring.splitlines():
        line = raw.strip()
        if not line:
            continue
        if ":" in line:
            key, _, value = line.partition(":")
            norm = key.strip().lower()
            if norm.startswith("one-line "):
                norm = norm[len("one-line "):]
            out[norm] = value.strip()
        elif "\u2014" in line:
            name, _, author = line.partition("\u2014")
            out.setdefault("filename", name.strip())
            out.setdefault("author", author.strip())
        else:
            out.setdefault("purpose", line)
    return out


def canonical_json(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def compute_seal(domain: str, content: bytes) -> str:
    h = hashlib.sha3_256()
    h.update(domain.encode("utf-8"))
    h.update(SEP)
    h.update(content)
    return h.hexdigest()


def file_seal(path: Path) -> str:
    return compute_seal(DOMAIN, path.read_bytes())


def check_header(path: Path) -> Tuple[bool, List[str]]:
    problems: List[str] = []
    source = read_source(path)
    line = docstring_line(source)
    if line < 0:
        problems.append("no module docstring")
        return False, problems
    if line != 2:
        problems.append(f"docstring at line {line}; expected 2 (after shebang)")
    fields = parse_header(docstring_text(source))
    for field in REQUIRED_FIELDS:
        if field not in fields:
            problems.append(f"missing header field: {field}")
    return (len(problems) == 0), problems


def emit_jsonl(events: Iterable[Dict[str, Any]]) -> str:
    lines = [json.dumps(ev, ensure_ascii=False) for ev in events]
    return "\n".join(lines) + "\n"


def _box_row(width: int, text: str) -> str:
    return "\u2551" + text.ljust(width) + "\u2551"


def emit_footer() -> str:
    width = 70
    top = "\u2554" + "\u2550" * width + "\u2557"
    mid = "\u2560" + "\u2550" * width + "\u2563"
    bot = "\u255a" + "\u2550" * width + "\u255d"

    version_rows = [
        _box_row(width, f"  {'schema:':<12} {SCHEMA}"),
        _box_row(width, f"  {'contract:':<12} three-files-contract.yaml  {CONTRACT_VERSION}"),
        _box_row(width, f"  {'domain:':<12} {DOMAIN}"),
        _box_row(width, f"  {'ast_header:':<12} {AST_HEADER_VERSION}"),
        _box_row(width, f"  {'jsonl:':<12} one event per line, no blank lines"),
    ]
    legend_rows = [
        _box_row(width, f"  {k + ':':<12} {v}") for k, v in LEGEND.items()
    ]
    lines = [
        top,
        _box_row(width, "  \u2500\u2500 version \u2500\u2500"),
        mid,
        *version_rows,
        mid,
        _box_row(width, "  \u2500\u2500 legend \u2500\u2500"),
        *legend_rows,
        bot,
    ]
    return "\n".join(lines) + "\n"


def cmd_check(path: Path) -> int:
    ok, problems = check_header(path)
    events = [
        {"type": "CHECK", "path": str(path), "ok": ok, "problems": problems},
        {"type": "SEAL", "path": str(path), "domain": DOMAIN, "digest": file_seal(path)},
    ]
    sys.stdout.write(emit_jsonl(events))
    return 0 if ok else 1


def cmd_header(path: Path) -> int:
    text = docstring_text(read_source(path))
    sys.stdout.write(text.rstrip() + "\n")
    return 0


def cmd_seal(path: Path) -> int:
    sys.stdout.write(file_seal(path) + "\n")
    return 0


def cmd_footer(_: Path) -> int:
    sys.stdout.write(emit_footer())
    return 0


def usage() -> int:
    sys.stderr.write("usage: format.py {check|header|seal|footer} <path>\n")
    return 2


def main(argv: List[str]) -> int:
    if len(argv) < 3:
        return usage()
    cmd, target = argv[1], argv[2]
    path = Path(target)
    if cmd in ("check", "header", "seal") and not path.exists():
        sys.stderr.write(f"no such file: {path}\n")
        return 1
    dispatch = {
        "check": cmd_check,
        "header": cmd_header,
        "seal": cmd_seal,
        "footer": cmd_footer,
    }
    fn = dispatch.get(cmd)
    if fn is None:
        return usage()
    return fn(path)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
