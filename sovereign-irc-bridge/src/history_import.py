# SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
# SPDX-License-Identifier: MIT
"""One-shot import of the JSONL ``/llm`` history into the SQLite backend.

    cd sovereign-irc-bridge
    python -m src.history_import --from jsonl --to sqlite \\
        [--src llm_history.jsonl] [--db llm_history.sqlite3] [--skip-stubs] [--json]

* The JSONL source is only ever opened for reading; it is never modified.
* Idempotent: every message carries a dedupe key (sha256 of session + ts +
  role + content), so running it again inserts nothing new.
* Everything is imported by default. ``--skip-stubs`` drops only complete
  test-stub pairs (user "what is the brain doing?" immediately followed in the
  same session by assistant "Lane L3 is busiest.") that unit tests used to
  write into the live file before PR #166. The counts are always reported.
* The whole import is one transaction: it either lands completely or not at all.

Defaults come from the bridge env: ``--src`` = LLM_HISTORY_PATH,
``--db`` = LLM_HISTORY_DB (else ``llm_history.sqlite3`` next to the source).
Exit status: 0 ok, 1 import failed (details on stderr), 2 bad arguments.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from src import llm_chat, llm_history_sqlite

STUB_PROMPT = "what is the brain doing?"
STUB_REPLY = "Lane L3 is busiest."

Row = Tuple[str, str, str, str, Optional[str], Optional[str]]


def read_jsonl(src: Path) -> Tuple[List[Dict[str, Any]], int]:
    """→ (dict rows in file order, unparseable line count). Read-only."""
    rows: List[Dict[str, Any]] = []
    bad = 0
    with src.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                bad += 1
                continue
            if isinstance(row, dict):
                rows.append(row)
            else:
                bad += 1
    return rows, bad


def _is_stub_pair(prev: Optional[Dict[str, Any]], row: Dict[str, Any]) -> bool:
    return (prev is not None and row.get("role") == "assistant" and row.get("content") == STUB_REPLY
            and prev.get("role") == "user" and prev.get("content") == STUB_PROMPT
            and llm_chat._row_session(prev) == llm_chat._row_session(row))


def plan(rows: List[Dict[str, Any]], *, skip_stubs: bool) -> Tuple[List[Row], Dict[str, int]]:
    """Map JSONL rows → store rows, counting stubs and rows that cannot be stored."""
    counts = {"stub_pairs": 0, "stub_pairs_skipped": 0, "bad_rows": 0}
    keep = [True] * len(rows)
    last_in_session: Dict[str, int] = {}
    for i, row in enumerate(rows):
        sess = llm_chat._row_session(row)
        j = last_in_session.get(sess)
        if j is not None and keep[j] and _is_stub_pair(rows[j], row):
            counts["stub_pairs"] += 1
            if skip_stubs:
                keep[i] = keep[j] = False
                counts["stub_pairs_skipped"] += 1
        last_in_session[sess] = i
    out: List[Row] = []
    for row, k in zip(rows, keep):
        if not k:
            continue
        role, content, ts = row.get("role"), row.get("content"), row.get("ts")
        if role not in llm_history_sqlite.ROLES or not isinstance(content, str):
            counts["bad_rows"] += 1
            continue
        fmt = row.get("format") if isinstance(row.get("format"), str) else None
        thinking = row.get("thinking") if isinstance(row.get("thinking"), str) else None
        out.append((llm_chat._row_session(row), role, content, ts if isinstance(ts, str) else "",
                    fmt, thinking))
    return out, counts


def run(src: Path, db: Path, *, skip_stubs: bool = False) -> Dict[str, Any]:
    """Import ``src`` into ``db``. Raises RuntimeError if the store write fails."""
    before = hashlib.sha256(src.read_bytes()).hexdigest()
    rows, bad_lines = read_jsonl(src)
    store_rows, counts = plan(rows, skip_stubs=skip_stubs)
    store = llm_history_sqlite.SqliteHistory(db)
    res = store.import_rows(store_rows)
    if res is None:
        raise RuntimeError(f"import into {db} failed (see log); nothing was written")
    after = hashlib.sha256(src.read_bytes()).hexdigest()
    if after != before:  # pragma: no cover - we never write it; guard against surprises
        raise RuntimeError(f"{src} changed during import")
    sessions = sorted({r[0] for r in store_rows})
    return {
        "src": str(src), "db": str(db), "src_sha256": before,
        "rows_read": len(rows), "bad_lines": bad_lines, **counts,
        "rows_to_import": len(store_rows), **res, "sessions": sessions,
        "stats": store.stats(),
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m src.history_import", description=__doc__.split("\n")[0])
    ap.add_argument("--from", dest="src_kind", choices=["jsonl"], required=True)
    ap.add_argument("--to", dest="dst_kind", choices=["sqlite"], required=True)
    ap.add_argument("--src", type=Path, default=None, help="JSONL file (default LLM_HISTORY_PATH)")
    ap.add_argument("--db", type=Path, default=None, help="SQLite file (default LLM_HISTORY_DB)")
    ap.add_argument("--skip-stubs", action="store_true",
                    help=f"skip complete {STUB_PROMPT!r} / {STUB_REPLY!r} test-stub pairs")
    ap.add_argument("--json", action="store_true", help="print the report as JSON")
    args = ap.parse_args(argv)
    src = args.src or llm_chat.history_path()
    if src is None or not src.is_file():
        print(f"history_import: source JSONL not found: {src}", file=sys.stderr)
        return 2
    db = args.db or llm_chat.history_db_path() or src.with_suffix(".sqlite3")
    if db.resolve() == src.resolve():
        print("history_import: --db must differ from --src", file=sys.stderr)
        return 2
    try:
        rep = run(src, db, skip_stubs=args.skip_stubs)
    except (OSError, RuntimeError) as exc:
        print(f"history_import: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(rep, indent=2, ensure_ascii=False))
    else:
        for k, v in rep.items():
            print(f"{k}: {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
