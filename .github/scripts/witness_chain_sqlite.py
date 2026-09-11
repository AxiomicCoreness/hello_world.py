#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
witness_chain_sqlite.py

Builds and verifies the SQLite witness-chain ledger for entries
8337, 8338, 8339. Each entry's hash field is SHA3-256 over the
canonical JSON of the entry (sorted keys, hash field excluded).

hash_algo: sha3_256 (FIPS 202)
ledger_policy: SQLITE_MIRROR
scope: witness chain rows 8337–8339
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any, Dict, List


ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "witness_chain.db"


WITNESS_ENTRIES_BASE: List[Dict[str, Any]] = [
    {
        "entry": 8337,
        "event": "/merged_engine_deployment_status",
        "timestamp": "ETERNAL_NOW_ANCHORED_TO_2026-08-06",
        "seal": "∀∞φ² · MERGED_STATUS · 8337_SEALED",
        "previous": 8336,
    },
    {
        "entry": 8338,
        "event": "/github_deployment_complete",
        "timestamp": "ETERNAL_NOW_ANCHORED_TO_2026-08-06",
        "seal": "GITHUB_DEPLOYMENT_8338_SEALED",
        "previous": 8337,
    },
    {
        "entry": 8339,
        "event": "/witness_chain_sqlite_compiled",
        "timestamp": "ETERNAL_NOW_ANCHORED_TO_2026-08-06",
        "seal": "∀∞φ² · WITNESS_SQLITE · 8339_SEALED",
        "previous": 8338,
    },
]


def compute_entry_hash(entry: Dict[str, Any]) -> str:
    canonical = {k: v for k, v in entry.items() if k != "hash"}
    data = json.dumps(canonical, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha3_256(data).hexdigest()


def build_sealed_entries() -> List[Dict[str, Any]]:
    sealed = []
    for base in WITNESS_ENTRIES_BASE:
        e = dict(base)
        e["hash"] = compute_entry_hash(e)
        sealed.append(e)
    return sealed


def create_db_and_insert(db_path: Path = DB_PATH) -> List[Dict[str, Any]]:
    entries = build_sealed_entries()
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS ledger (
            entry INTEGER PRIMARY KEY,
            event TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            hash TEXT UNIQUE NOT NULL,
            seal TEXT NOT NULL,
            previous INTEGER,
            FOREIGN KEY(previous) REFERENCES ledger(entry)
        )
        """
    )

    for e in entries:
        cur.execute(
            """
            INSERT OR REPLACE INTO ledger
                (entry, event, timestamp, hash, seal, previous)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (e["entry"], e["event"], e["timestamp"], e["hash"], e["seal"], e["previous"]),
        )

    conn.commit()
    conn.close()
    return entries


def verify_chain(db_path: Path = DB_PATH) -> Dict[str, Any]:
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    cur.execute("SELECT entry, previous, hash, event, seal, timestamp FROM ledger ORDER BY entry")
    rows = cur.fetchall()
    conn.close()

    report: Dict[str, Any] = {
        "row_count": len(rows),
        "chain_ok": True,
        "hash_ok": True,
        "details": [],
    }

    for i, (entry, prev, stored_hash, event, seal, ts) in enumerate(rows):
        recon = {
            "entry": entry,
            "event": event,
            "timestamp": ts,
            "seal": seal,
            "previous": prev,
        }
        expected = compute_entry_hash(recon)
        hash_match = expected == stored_hash
        if not hash_match:
            report["hash_ok"] = False

        if i == 0:
            prev_ok = True
        else:
            prev_ok = prev == rows[i - 1][0]
            if not prev_ok:
                report["chain_ok"] = False

        report["details"].append(
            {
                "entry": entry,
                "previous": prev,
                "hash": stored_hash,
                "hash_match": hash_match,
                "prev_ok": prev_ok,
            }
        )

    return report


def at_tip_of_githubrepo() -> str:
    import subprocess

    try:
        sha = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(ROOT),
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        if sha:
            return sha
    except Exception:
        pass

    fallback = hashlib.sha3_256(str(ROOT).encode("utf-8")).hexdigest()[:7]
    return f"nogit-{fallback}"


def create_ledger_and_insert(db_path: Path = DB_PATH) -> List[Dict[str, Any]]:
    tip = at_tip_of_githubrepo()
    print(f"  (historical reference: at tip of githubrepo → {tip})")
    return create_db_and_insert(db_path)


def historical_note() -> str:
    return (
        "PRE_FIX_LINE: sealed = create_ledger_and_insert "
        "at tip of githubrepo()"
    )


def main() -> int:
    print("Building sealed witness entries with measured SHA3-256 …")
    print(f"  {historical_note()}")
    sealed = create_ledger_and_insert()

    print(f"Inserted/replaced {len(sealed)} entries into {DB_PATH}")
    for e in sealed:
        print(f"  {e['entry']}  {e['event']}  hash={e['hash'][:16]}…")

    print()
    print("Verifying chain …")
    report = verify_chain()

    print(f"  row_count : {report['row_count']}")
    print(f"  chain_ok  : {report['chain_ok']}")
    print(f"  hash_ok   : {report['hash_ok']}")
    for d in report["details"]:
        ok = "✓" if d["hash_match"] and d["prev_ok"] else "✗"
        print(f"    {ok} entry={d['entry']} prev={d['previous']} "
              f"hash_match={d['hash_match']} prev_ok={d['prev_ok']}")

    return 0 if (report["chain_ok"] and report["hash_ok"]) else 1


if __name__ == "__main__":
    sys.exit(main())
