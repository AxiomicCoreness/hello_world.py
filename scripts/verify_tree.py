#!/usr/bin/env python3
"""
scripts/verify_tree.py — Tree Integrity Guard

Derived reading, named by Commander 2026-09-20:
    tree       = filesystem tree
    parent     = containing directory
    fragment   = any `[[ref]]` line
    root       = repo root (directory containing .git)

Two derived conventions, marked so provenance is visible:
    C1. Fragment references resolve relative to the repo root,
        not relative to the containing file.
    C2. Fragment syntax is `[[path]]` with optional `#anchor`,
        matched by regex \\[\\[([^\\[]+)\\]\\].

Checks:
    1. root-uniqueness   — exactly one .git directory under root
    2. symlink-cycles    — no directory symlink cycles; no escape from root
    3. reachability      — tautological on a filesystem tree; recorded only
    4. fragment-refs     — every [[ref]] resolves to an existing path

Exit codes:
    0 — all checks pass
    1 — one or more violations
    2 — setup error (not a git repo)

Ledger policy: NO_LEDGER_WRITE
MCP: unfilled · dual ASGI 127.0.0.1:8024
"""
from __future__ import annotations
import os
import re
import sys
from pathlib import Path
from typing import List, Tuple

FRAGMENT_RE = re.compile(r"\[\[([^\[]+)\]\]")

SKIP_DIRS = {
    ".git", "__pycache__", ".pytest_cache", ".mypy_cache",
    "node_modules", ".venv", "venv", "env", ".tox", ".nox",
    ".merge", ".worker-hooks",
}

SKIP_FILE_SUFFIXES = (
    ".pyc", ".pyo", ".so", ".dylib", ".dll", ".o", ".a",
    ".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip", ".tar", ".gz",
)

MAX_FILE_SIZE = 2 * 1024 * 1024  # 2 MiB — do not read larger files


def find_repo_root(start: Path) -> Path:
    p = start.resolve()
    for candidate in [p, *p.parents]:
        if (candidate / ".git").exists():
            return candidate
    raise RuntimeError(f"no .git found walking up from {start}")


def iter_paths(root: Path):
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in dirnames + filenames:
            yield Path(dirpath) / name


def check_root_uniqueness(root: Path) -> Tuple[bool, str]:
    git_dirs = [g for g in root.rglob(".git") if g.is_dir()]
    if len(git_dirs) == 1:
        return True, f"single root: {root}"
    return False, f"expected 1 .git directory, found {len(git_dirs)}"


def check_no_symlink_cycles(root: Path) -> Tuple[bool, List[str]]:
    problems: List[str] = []
    for p in iter_paths(root):
        if not p.is_symlink():
            continue
        try:
            target = p.resolve(strict=True)
        except (OSError, RuntimeError) as e:
            problems.append(f"dangling symlink: {p} -> {e}")
            continue
        try:
            target.relative_to(root)
        except ValueError:
            problems.append(f"symlink escapes root: {p} -> {target}")
    return len(problems) == 0, problems


def check_reachability(root: Path) -> Tuple[bool, List[str]]:
    # Tautological on a filesystem tree — kept to record the invariant.
    return True, []


def check_fragments(root: Path) -> Tuple[bool, List[str]]:
    problems: List[str] = []
    for p in iter_paths(root):
        if not p.is_file():
            continue
        if p.suffix.lower() in SKIP_FILE_SUFFIXES:
            continue
        try:
            if p.stat().st_size > MAX_FILE_SIZE:
                continue
        except OSError:
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            for m in FRAGMENT_RE.finditer(line):
                ref = m.group(1).strip()
                if not ref:
                    continue
                ref_path = ref.split("#", 1)[0].strip()
                if not ref_path:
                    continue
                target = (root / ref_path).resolve()
                if not target.exists():
                    rel = p.relative_to(root)
                    problems.append(f"{rel}:{lineno} -> [[{ref}]] unresolved")
    return len(problems) == 0, problems


def main() -> int:
    try:
        root = find_repo_root(Path.cwd())
    except RuntimeError as e:
        print(f"❌ {e}", file=sys.stderr)
        return 2

    print(f"root = {root}")
    print()

    ok_root, msg_root = check_root_uniqueness(root)
    print(f"{'OK' if ok_root else 'FAIL':5} root-uniqueness       {msg_root}")

    ok_cycle, cycle_problems = check_no_symlink_cycles(root)
    print(f"{'OK' if ok_cycle else 'FAIL':5} symlink-cycles        {len(cycle_problems)} problem(s)")
    for p in cycle_problems[:20]:
        print(f"      - {p}")

    ok_reach, _ = check_reachability(root)
    print(f"{'OK' if ok_reach else 'FAIL':5} reachability          (filesystem tautology)")

    ok_frag, frag_problems = check_fragments(root)
    print(f"{'OK' if ok_frag else 'FAIL':5} fragment-references   {len(frag_problems)} unresolved")
    for p in frag_problems[:40]:
        print(f"      - {p}")
    if len(frag_problems) > 40:
        print(f"      … and {len(frag_problems) - 40} more")

    print()
    all_ok = ok_root and ok_cycle and ok_reach and ok_frag
    if all_ok:
        print("✅ verify_tree: all checks pass")
        return 0
    print("❌ verify_tree: violations detected")
    return 1


if __name__ == "__main__":
    sys.exit(main())
