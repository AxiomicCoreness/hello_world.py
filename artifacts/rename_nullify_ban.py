#!/usr/bin/env python3
"""Search-and-replace incoming NULL_BAN instances with NULLIFY_BAN.

Dry-run by default. --apply writes bytes. Does not walk .md (sealed prose).
Does not issue a ledger seal.

Boundary: NULL_BAN matches as a prefix of a compound, so an incoming
NULL_BAN_12SIGMA / NULL_BAN_16SIGMA / any later NULL_BAN_* is rewritten.
A following letter or digit still blocks (NULL_BANx is not a compound).
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SCAN_SUFFIXES = {".py", ".yml", ".yaml"}
EXCLUDED_DIRS = {".git", "__pycache__", ".venv", "venv", "node_modules", ".mypy_cache"}

TOKEN_MAP = (
    ("NULL_BAN_16SIGMA", "NULLIFY_BAN_16SIGMA"),
    ("NULL_BAN_12SIGMA", "NULLIFY_BAN_12SIGMA"),
    ("NULL_BAN_FACTOR", "NULLIFY_BAN_FACTOR"),
    ("NULL_BAN_SIGMA", "NULLIFY_BAN_SIGMA"),
    ("NULL_BAN", "NULLIFY_BAN"),
    ("null_ban_sigma", "nullify_ban_sigma"),
    ("null_ban_threshold", "nullify_ban_threshold"),
    ("automaton_null_ban", "automaton_nullify_ban"),
    ("null_ban", "nullify_ban"),
    ("Null-Ban", "Nullify-Ban"),
    ("Null_Ban", "Nullify_Ban"),
    ("null-ban", "nullify-ban"),
)

PREFIX_RULES = (
    (re.compile(r"(?<![A-Za-z0-9_])NULL_BAN(?=_|[^A-Za-z0-9_]|$)"), "NULLIFY_BAN"),
    (re.compile(r"(?<![A-Za-z0-9_])null_ban(?=_|[^A-Za-z0-9_]|$)"), "nullify_ban"),
    (re.compile(r"(?<![A-Za-z0-9_])Null_Ban(?=_|[^A-Za-z0-9_]|$)"), "Nullify_Ban"),
    (re.compile(r"(?<![A-Za-z0-9_])Null-Ban(?=[^A-Za-z0-9_]|$)"), "Nullify-Ban"),
    (re.compile(r"(?<![A-Za-z0-9_])null-ban(?=[^A-Za-z0-9_]|$)"), "nullify-ban"),
)


def skipped(path: Path) -> bool:
    return any(part in EXCLUDED_DIRS for part in path.parts)


def candidates(root: Path) -> list[Path]:
    found = []
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix not in SCAN_SUFFIXES or skipped(path):
            continue
        text = path.read_bytes().decode("utf-8")
        if any(old in text for old, _ in TOKEN_MAP):
            found.append(path)
    return found


def rewrite(text: str) -> tuple[str, int]:
    count = 0
    for pattern, repl in PREFIX_RULES:
        text, n = pattern.subn(repl, text)
        count += n
    return text, count


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Replace incoming NULL_BAN instances")
    parser.add_argument("--root", default=".")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)
    root = Path(args.root)
    files = candidates(root)
    if not files:
        if root.is_dir():
            print("rename already applied; nothing to do")
            return 0
        print("REFUSING: root is not a directory")
        return 1
    changed = 0
    for path in files:
        text = path.read_bytes().decode("utf-8")
        new_text, n = rewrite(text)
        if n == 0:
            continue
        changed += 1
        print(f"{'APPLY' if args.apply else 'DRY'} {path}  replacements={n}")
        if args.apply:
            path.write_bytes(new_text.encode("utf-8"))
    print(f"files with tokens: {len(files)}  files rewritten: {changed}  apply={args.apply}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
