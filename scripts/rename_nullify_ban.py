#!/usr/bin/env python3
"""Search-and-replace incoming NULL_BAN instances with NULLIFY_BAN.

Dry-run by default. --apply writes bytes. Does not walk .md.
Does not rewrite this file. Does not walk ledger/ unless --include-ledger.
Does not issue a ledger seal.

Boundary fix: a leading underscore is part of the token, not a blocker.
shield_null_ban and SHIELD_NULL_BAN are incoming instances.
NULL_BANx still does not match. NULLIFY_BAN does not contain NULL_BAN.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SCAN_SUFFIXES = {".py", ".yml", ".yaml", ".json"}
EXCLUDED_DIRS = {".git", "__pycache__", ".venv", "venv", "node_modules", ".mypy_cache"}
PROTECTED_PARTS = {"Immutable"}
SELF_NAMES = {"rename_nullify_ban.py"}

# Intentionally unmatched: test_pipeline_null_ban. The leading underscore is the
# word boundary. Do not relax that lookbehind. Add an explicit map entry only
# if that test identifier itself must be renamed.
#
# Trailing underscore is not a blocker, so NULL_BAN_12SIGMA matches without a map entry.
PREFIX_RULES = (
    (re.compile(r"(?<![A-Za-z0-9_])NULL_BAN(?![A-Za-z0-9])"), "NULLIFY_BAN"),
    (re.compile(r"(?<![A-Za-z0-9_])null_ban(?![A-Za-z0-9])"), "nullify_ban"),
    (re.compile(r"(?<![A-Za-z0-9_])Null_Ban(?![A-Za-z0-9])"), "Nullify_Ban"),
    (re.compile(r"(?<![A-Za-z0-9_])Null-Ban(?![A-Za-z0-9])"), "Nullify-Ban"),
    (re.compile(r"(?<![A-Za-z0-9_])null-ban(?![A-Za-z0-9])"), "nullify-ban"),
)
DISCOVERY = re.compile(
    r"(?<![A-Za-z0-9_])(?:NULL_BAN|null_ban|Null_Ban|Null-Ban|null-ban)(?![A-Za-z0-9])"
)


def skipped(path: Path, include_ledger: bool) -> bool:
    if path.name in SELF_NAMES:
        return True
    if any(part in EXCLUDED_DIRS or part in PROTECTED_PARTS for part in path.parts):
        return True
    if path.name.startswith("ledger_") and path.name.endswith(".schema.json"):
        return True
    if not include_ledger and "ledger" in path.parts:
        return True
    return False


def candidates(root: Path, include_ledger: bool) -> list[Path]:
    found = []
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix not in SCAN_SUFFIXES or skipped(path, include_ledger):
            continue
        text = path.read_bytes().decode("utf-8")
        if DISCOVERY.search(text):
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
    parser.add_argument("--include-ledger", action="store_true")
    args = parser.parse_args(argv)
    root = Path(args.root)
    if not root.is_dir():
        print("REFUSING: root is not a directory")
        return 1
    files = candidates(root, args.include_ledger)
    if not files:
        print("rename already applied; nothing to do")
        return 0
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
