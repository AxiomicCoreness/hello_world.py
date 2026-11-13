#!/usr/bin/env python3
"""ledger_chore_finalize.py — run after a chore workflow writes ledger files, before it commits.

  python -I tools/ledger_chore_finalize.py --root .            # changed/new files from git status
  python -I tools/ledger_chore_finalize.py --root . FILE...    # explicit files

1. Append-only: a file already linked in ledger.chain.jsonl whose bytes changed is
   restored from HEAD (the rewrite is discarded, never committed).
2. prev_hash: a new entry with an empty or missing prev_hash gets the terminal hex of
   the seal of the nearest lower entry_index in ledger/ or ledger.v2/ (the convention the
   chained ledger.v2 entries use). The fill is skipped if it would turn a verified seal
   into an unverified one; such writers must fill prev_hash before they seal.
3. Index and chain: runs tools/ledger_index.py (write) and then --check, so the commit
   carries ledger_index.jsonl and the appended ledger.chain.jsonl link.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ledger_index
import ledger_seal
import yaml

HEX64 = re.compile(r"[0-9a-f]{64}")
PREV_LINE = re.compile(r"^prev_hash:.*$", re.MULTILINE)
SEAL_LINE = re.compile(r"^seal:", re.MULTILINE)


def git(root: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True).stdout


def ledger_files(root: Path) -> list[str]:
    return [p.relative_to(root).as_posix() for p in ledger_index.list_files(root)]


def changed_files(root: Path, known: list[str]) -> list[str]:
    out = git(root, "status", "--porcelain", "--untracked-files=all", "--", *ledger_index.FOLDERS)
    paths = []
    for line in out.splitlines():
        p = line[3:].strip().strip('"')
        if " -> " in p:
            p = p.split(" -> ", 1)[1]
        paths.append(p)
    ks = set(known)
    return [p for p in paths if p in ks]


def load(root: Path, rel: str) -> dict[str, Any] | None:
    try:
        d = yaml.safe_load((root / rel).read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return None
    return d if isinstance(d, dict) else None


def seal_hex(d: dict[str, Any]) -> str | None:
    m = HEX64.findall(str(d.get("seal", "")).lower())
    return m[-1] if m else None


def predecessor_hash(root: Path, n: int, rel: str, files: list[str]) -> str | None:
    best = None
    for f in files:
        if f == rel:
            continue
        d = load(root, f)
        if not d:
            continue
        k = d.get("entry_index")
        if not isinstance(k, int) or isinstance(k, bool) or k >= n:
            continue
        h = seal_hex(d)
        if h and (best is None or k > best[0]):
            best = (k, h)
    return best[1] if best else None


def fill_prev_hash(root: Path, rel: str, files: list[str]) -> str:
    d = load(root, rel)
    if not d:
        return "skip (not a mapping)"
    n = d.get("entry_index")
    if not isinstance(n, int) or isinstance(n, bool):
        return "skip (no integer entry_index)"
    if d.get("prev_hash") not in (None, ""):
        return "kept existing prev_hash"
    h = predecessor_hash(root, n, rel, files)
    if not h:
        return "skip (no sealed predecessor)"
    before = ledger_seal.verify_entry(d)["status"]
    after = ledger_seal.verify_entry({**d, "prev_hash": h})["status"]
    if before == ledger_seal.VERIFIED and after != ledger_seal.VERIFIED:
        return "skip (seal covers prev_hash; writer must fill it before sealing)"
    text = (root / rel).read_text(encoding="utf-8")
    line = f"prev_hash: {h}"
    if PREV_LINE.search(text):
        text = PREV_LINE.sub(line, text, count=1)
    elif SEAL_LINE.search(text):
        text = SEAL_LINE.sub(line + "\nseal:", text, count=1)
    else:
        text = text.rstrip("\n") + "\n" + line + "\n"
    (root / rel).write_text(text, encoding="utf-8")
    return f"filled prev_hash {h}"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", default=".")
    ap.add_argument("files", nargs="*")
    a = ap.parse_args(argv)
    root = Path(a.root).resolve()
    files = ledger_files(root)
    targets = [Path(f).as_posix() for f in a.files] if a.files else changed_files(root, files)
    chained = {c["path"]: c["sha256"] for c in ledger_index.load_chain(root)}
    for rel in targets:
        if not (root / rel).exists():
            if rel in chained:
                git(root, "checkout", "HEAD", "--", rel)
                print(f"::warning::{rel}: deleted but chained; restored (ledger is append-only)")
            continue
        if rel in chained:
            if hashlib.sha256((root / rel).read_bytes()).hexdigest() != chained[rel]:
                git(root, "checkout", "HEAD", "--", rel)
                print(f"::warning::{rel}: rewrite discarded, restored from HEAD (ledger is append-only)")
            continue
        print(f"{rel}: {fill_prev_hash(root, rel, files)}")
    if ledger_index.main(["--root", str(root)]) != 0:
        return 1
    return ledger_index.main(["--root", str(root), "--check"])


if __name__ == "__main__":
    sys.exit(main())
