#!/usr/bin/env python3
"""Add a new file from an existing file.

Usage: python3 scripts/add_from_edit.py SOURCE DEST

Copies SOURCE to DEST. Refuses to overwrite DEST. Does not edit the
55-name slot table. A second copy of that table would fork the formula.
"""
from __future__ import annotations

import sys
from pathlib import Path


def add_from_edit(source: Path, dest: Path) -> None:
    if not source.is_file():
        raise FileNotFoundError(source)
    if dest.exists():
        raise FileExistsError(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(source.read_bytes())


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print("usage: add_from_edit.py SOURCE DEST", file=sys.stderr)
        return 2
    add_from_edit(Path(argv[1]), Path(argv[2]))
    print(argv[2])
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
