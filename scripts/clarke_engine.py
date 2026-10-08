#!/usr/bin/env python3
"""ClarkeYoursaTee engine. SQLite and stdlib only. kubectl is not required.

Running twice writes the same rows. A missing cluster is recorded, not applied.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "engine.db"

PACKET = {
    "packet": 1,
    "layout": "simd-batch-step",
    "manifest": "kubernetes/cronjob-simd-step.yaml",
    "kubectl": False,
    "schedule": "0 */6 * * *",
    "concurrencyPolicy": "Forbid",
    "phase_deg": 202.6,
    "zeta_bound": 2.366,
}


def sha3(value: str) -> str:
    return hashlib.sha3_256(value.encode("utf-8")).hexdigest()


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS witness (
            entry_index INTEGER PRIMARY KEY,
            event TEXT NOT NULL,
            hash TEXT NOT NULL,
            prev_hash TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS packet (
            packet INTEGER PRIMARY KEY,
            body TEXT NOT NULL,
            hash TEXT NOT NULL,
            kubectl INTEGER NOT NULL
        )
        """
    )
    return conn


def seed(conn: sqlite3.Connection) -> None:
    rows = [
        (8337, "/merged_engine_deployment_status"),
        (8338, "/github_deployment_complete"),
        (8339, "/witness_chain_sqlite_compiled"),
    ]
    prev = ""
    for index, event in rows:
        digest = sha3(f"{index}|{event}|{prev}")
        conn.execute(
            """
            INSERT INTO witness (entry_index, event, hash, prev_hash)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(entry_index) DO UPDATE SET
                event=excluded.event,
                hash=excluded.hash,
                prev_hash=excluded.prev_hash
            WHERE witness.hash != excluded.hash
            """,
            (index, event, digest, prev),
        )
        prev = digest
    body = json.dumps(PACKET, sort_keys=True)
    conn.execute(
        """
        INSERT INTO packet (packet, body, hash, kubectl)
        VALUES (1, ?, ?, 0)
        ON CONFLICT(packet) DO UPDATE SET
            body=excluded.body,
            hash=excluded.hash,
            kubectl=excluded.kubectl
        WHERE packet.hash != excluded.hash
        """,
        (body, sha3(body)),
    )
    conn.commit()


def report(conn: sqlite3.Connection) -> dict:
    rows = conn.execute(
        "SELECT entry_index, prev_hash, hash FROM witness ORDER BY entry_index"
    ).fetchall()
    prev = ""
    intact = True
    for _index, previous, digest in rows:
        if previous != prev:
            intact = False
        prev = digest
    packet = conn.execute("SELECT kubectl, hash FROM packet WHERE packet=1").fetchone()
    return {
        "db": str(DB_PATH),
        "kubectl": bool(packet[0]) if packet else False,
        "kubectl_bin": shutil.which("kubectl") is not None,
        "rows": len(rows),
        "chain_ok": intact and len(rows) == 3,
        "packet_hash": packet[1] if packet else "",
    }


def main() -> int:
    if shutil.which("kubectl"):
        print("kubectl present; engine still does not call it", file=sys.stderr)
    conn = connect()
    seed(conn)
    first = report(conn)
    seed(conn)
    second = report(conn)
    first["idempotent"] = first == second
    print(json.dumps(first, sort_keys=True))
    return 0 if first["idempotent"] and first["chain_ok"] and not first["kubectl"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
