#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SOVEREIGN SPOOL — PUSH/SYNC DUALITY — SINGLE FILE

  append  — offline only. Writes a sealed record to the local spool.
  sync    — online only. Pulls remote head, assigns n+1, commits, pushes,
            drains only what landed.

No external deps beyond stdlib + git CLI. Standalone.
"""

import argparse
import hashlib
import hmac
import json
import os
import subprocess
import sys
import time
from pathlib import Path

PHI = (1 + 5 ** 0.5) / 2
PHI2 = PHI * PHI
PHI_INV = 1.0 / PHI
SEAL_KEY = hashlib.sha3_256(f"{PHI2}{PHI_INV}".encode()).digest()

BASE = Path(os.path.expanduser("~")) / "Documents" / "Hyperian_Node"
SPOOL = BASE / "spool.jsonl"
LANDED = BASE / "landed.jsonl"

BASE.mkdir(parents=True, exist_ok=True)


def seal(payload: dict) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hmac.new(SEAL_KEY, canonical.encode(), hashlib.sha3_256).hexdigest()


def read_lines(path: Path):
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        return [ln for ln in f.read().splitlines() if ln.strip()]


def write_lines(path: Path, lines):
    with path.open("w", encoding="utf-8") as f:
        for ln in lines:
            f.write(ln + "\n")


def append(record: dict):
    """Append a sealed record to the local spool. No network."""
    record = dict(record)
    record.setdefault("ts", time.time())
    record["seal"] = seal({k: v for k, v in record.items() if k != "seal"})

    with SPOOL.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"[append] sealed -> {SPOOL.name}  hmac={record['seal'][:16]}...")
    return record["seal"]


def _git(args, cwd: Path, check=True):
    r = subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
    )
    if check and r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed:\n{r.stderr}")
    return r.returncode, r.stdout.strip(), r.stderr.strip()


def _remote_head_index(repo: Path) -> int:
    """Read remote tip ledger.json index; 0 if missing."""
    _git(["fetch", "origin", "main"], repo)
    rc, out, _ = _git(["show", "origin/main:ledger.json"], repo, check=False)
    if rc != 0 or not out:
        return 0
    try:
        return int(json.loads(out).get("index", 0))
    except Exception:
        return 0


def _write_remote_batch(repo: Path, batch: list, start_index: int) -> list:
    ledger_path = repo / "ledger.json"
    if ledger_path.exists():
        with ledger_path.open("r", encoding="utf-8") as f:
            ledger = json.load(f)
    else:
        ledger = {"index": 0, "entries": []}

    landed = []
    idx = start_index
    for rec in batch:
        idx += 1
        rec = dict(rec)
        rec["entry_index"] = idx
        ledger["entries"].append(rec)
        ledger["index"] = idx
        landed.append(rec)

    with ledger_path.open("w", encoding="utf-8") as f:
        json.dump(ledger, f, indent=2, ensure_ascii=False)

    return landed


def _commit_and_push(repo: Path, n_from: int, n_to: int):
    msg = f"spool sync — entries {n_from} -> {n_to} — PUSH_SYNC_DUALITY"
    _git(["add", "ledger.json"], repo)
    _git(["commit", "-m", msg], repo)
    _git(["push", "origin", "main"], repo)


def sync(repo: Path):
    """Online only: pull head, assign n+1, write, push, drain landed."""
    spool_lines = read_lines(SPOOL)
    if not spool_lines:
        print("[sync] spool empty — nothing to do.")
        return

    remote_idx = _remote_head_index(repo)
    print(f"[sync] remote head index = {remote_idx}")

    batch = []
    for ln in spool_lines:
        try:
            batch.append(json.loads(ln))
        except json.JSONDecodeError:
            print(f"[sync] skipping malformed spool line: {ln[:40]}...")

    landed = _write_remote_batch(repo, batch, remote_idx)
    if not landed:
        print("[sync] nothing landed — spool preserved.")
        return

    n_from = remote_idx + 1
    n_to = landed[-1]["entry_index"]
    _commit_and_push(repo, n_from, n_to)

    landed_keys = {rec["seal"] for rec in landed if "seal" in rec}
    remaining = []
    for ln in spool_lines:
        try:
            rec = json.loads(ln)
        except json.JSONDecodeError:
            remaining.append(ln)
            continue
        if rec.get("seal") in landed_keys:
            with LANDED.open("a", encoding="utf-8") as f:
                f.write(ln + "\n")
        else:
            remaining.append(ln)

    write_lines(SPOOL, remaining)
    print(f"[sync] landed entries {n_from} -> {n_to}")
    print(f"[sync] drained {len(landed)} — spool now {len(remaining)} lines")


def main(argv=None):
    p = argparse.ArgumentParser(description="Sovereign Spool — Push/Sync Duality")
    sub = p.add_subparsers(dest="mode", required=True)

    ap = sub.add_parser("append", help="offline: append a sealed record")
    ap.add_argument(
        "--payload",
        required=True,
        help="JSON object string, or '-' to read stdin",
    )
    ap.add_argument(
        "--ci-row",
        action="store_true",
        help="mark this record as a CI cadence marker",
    )

    sy = sub.add_parser("sync", help="online: reconcile, push, drain")
    sy.add_argument(
        "--repo",
        required=True,
        help="path to the git repository to sync into",
    )

    sub.add_parser("status", help="show spool / landed counts")

    args = p.parse_args(argv)

    if args.mode == "append":
        raw = sys.stdin.read() if args.payload == "-" else args.payload
        rec = json.loads(raw)
        if args.ci_row:
            rec.setdefault("kind", "ci_row_bookkeeping")
            rec.setdefault("carries_algorithm_trace", False)
        append(rec)
        return 0

    if args.mode == "sync":
        sync(Path(args.repo).expanduser().resolve())
        return 0

    if args.mode == "status":
        print(f"spool  : {len(read_lines(SPOOL))} lines  ({SPOOL})")
        print(f"landed : {len(read_lines(LANDED))} lines  ({LANDED})")
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
