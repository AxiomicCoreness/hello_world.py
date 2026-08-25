#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🜁∀ WITNESS CHAIN — SQLITE COMPILER — ENTRY 8339
Honest measured SHA3-256 digests only. No placeholder hashes.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "witness_chain.db"

# Canonical entries (hash field omitted; computed at runtime)
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
    """SHA3-256 of canonical JSON (sorted keys, hash field excluded)."""
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
    cur.execute("SELECT entry, previous, hash, event, seal FROM ledger ORDER BY entry")
    rows = cur.fetchall()
    conn.close()

    report = {
        "row_count": len(rows),
        "chain_ok": True,
        "hash_ok": True,
        "details": [],
    }

    for i, (entry, prev, stored_hash, event, seal) in enumerate(rows):
        recon = {
            "entry": entry,
            "event": event,
            "timestamp": "ETERNAL_NOW_ANCHORED_TO_2026-08-06",
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


if __name__ == "__main__":
    print("Building sealed witness entries with measured SHA3-256 …")
    sealed = create_db_and_insert()
    for e in sealed:
        print(f"  entry {e['entry']}: hash={e['hash']} seal={e['seal']}")  # full hash, no truncation

    print(f"\nDatabase: {DB_PATH}")
    report = verify_chain()
    print(json.dumps(report, indent=2))

    if report["chain_ok"] and report["hash_ok"] and report["row_count"] == 3:
        print("\n✅ WITNESS_CHAIN 8337→8338→8339 — hashes match, previous pointers continuous")
    else:
        print("\n⚠️ Verification incomplete — inspect report above")
