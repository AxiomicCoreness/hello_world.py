#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pre-main walk-up markdown appender — ledger 9163.

POLICY:
  FILLED = False
  Never bind. Never 0.0.0.0. Dual ASGI remains 127.0.0.1:8024.
  Stop at repository root (.git) or a forbidden ancestor.
  Do not walk to filesystem root.
  Dry-run unless --apply.
  Append-only and idempotent when applying.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Iterable, List, Tuple

FILLED = False
BIND = "127.0.0.1"
DUAL_ASGI = "127.0.0.1:8024"
FORBIDDEN_STOPS = frozenset({
    Path("/"),
    Path("/home"),
    Path("/root"),
    Path("/usr"),
    Path("/etc"),
    Path("/var"),
    Path("/opt"),
    Path("/tmp"),
})
DEFAULT_CHANGE = (
    "\n\n<!-- APPENDED BY WALK-UP STUB · 9163 · APPEND_ONLY -->\n"
)


def _is_repo_root(directory: Path) -> bool:
    return (directory / ".git").exists()


def _forbidden(directory: Path) -> bool:
    resolved = directory.resolve()
    return resolved in FORBIDDEN_STOPS or resolved.parent == resolved


def ancestor_dirs(start_dir: Path) -> List[Path]:
    current = start_dir.resolve()
    out: List[Path] = []
    while True:
        if _forbidden(current):
            break
        out.append(current)
        if _is_repo_root(current):
            break
        parent = current.parent
        if parent == current:
            break
        current = parent
    return out


def md_files(directories: Iterable[Path]) -> List[Path]:
    found: List[Path] = []
    for directory in directories:
        found.extend(sorted(p for p in directory.glob("*.md") if p.is_file()))
    return found


def already_appended(path: Path, change_text: str) -> bool:
    data = path.read_bytes()
    tail = change_text.encode("utf-8")
    return data.endswith(tail)


def walk_up_append_md(
    change_text: str,
    start_dir: str = ".",
    apply: bool = False,
) -> Tuple[int, int]:
    if not change_text:
        raise ValueError("change_text must not be empty")
    dirs = ancestor_dirs(Path(start_dir))
    targets = md_files(dirs)
    appended = 0
    skipped = 0
    for path in targets:
        try:
            if already_appended(path, change_text):
                print(f"skip already-present {path}")
                skipped += 1
                continue
            if not apply:
                print(f"dry-run would-append {path}")
                skipped += 1
                continue
            with path.open("a", encoding="utf-8") as handle:
                handle.write(change_text)
            print(f"appended {path}")
            appended += 1
        except OSError as exc:
            print(f"failed {path}: {exc}")
    return appended, skipped


def main() -> int:
    parser = argparse.ArgumentParser(description="Constrained walk-up markdown appender")
    parser.add_argument("--start-dir", default=".")
    parser.add_argument("--change-text", default=DEFAULT_CHANGE)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="actually append; default is dry-run",
    )
    args = parser.parse_args()
    appended, skipped = walk_up_append_md(
        args.change_text,
        start_dir=args.start_dir,
        apply=args.apply,
    )
    print(
        f"filled={FILLED} bind={BIND} dual_asgi={DUAL_ASGI} "
        f"appended={appended} skipped={skipped} apply={args.apply}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
