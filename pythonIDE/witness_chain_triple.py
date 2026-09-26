#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pythonIDE/witness_chain_triple.py

pythonIDE-local snippet. Not Pythonista. Does not bind Dual ASGI.
Does not fill MCP. Does not start uvicorn.

The "triple" is the witness chain 8337 → 8338 → 8339 — the smallest
coherent unit for exercising the ledger's Regime B canonicalisation.

hash_algo:          sha3_256 (FIPS 202)
canonical_regime:   B  — body-hash
  serialisation:    json.dumps(body, sort_keys=True,
                               separators=(",", ":"),
                               ensure_ascii=False)
  body:             entry minus the "hash" field
  verifier:         verify_ledger.py  (S5b)
scope:              witness rows 8337, 8338, 8339
ledger_policy:      SQLITE_MIRROR — local only, does not rewrite ledger/*.yaml

Historical claim (preserved verbatim, not enforced by this file):
  "e.g github-actions Bot excluded from entire site:
   GitHub.com/AxiomicCoreness/hello_world.py repo editing"

  Status of that claim: DECLARED_INTENT, NOT_ENFORCED_HERE.
  A Python docstring cannot restrict repository access. The mechanisms
  that can are:
    - .github/CODEOWNERS          (required review)
    - workflow `permissions:`     (bot token scope)
    - branch protection rules     (repo settings, UI only)
  This file records the intent. It does not implement it.

Policy compliance:
  - No ledger/*.yaml is rewritten by this file.
  - POLICY.md is not touched.
  - Sealed bands 0000–9223 stay immutable.
  - Append-only convention preserved; this file is a mirror, not a source.

Gearbox (do not start from here):
  uvicorn fastMCP.gearbox:app --host 127.0.0.1 --port 8024
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
from pathlib import Path

import yaml

REGIME = "B"
EXCLUDED_FIELDS = ("hash",)
TRIPLE = (8337, 8338, 8339)


def canonical_body(doc: dict) -> str:
    """Regime B body-hash serialisation: entry minus 'hash', sorted keys."""
    body = {k: v for k, v in doc.items() if k not in EXCLUDED_FIELDS}
    return json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def body_hash(doc: dict) -> str:
    payload = canonical_body(doc).encode("utf-8")
    return hashlib.sha3_256(payload).hexdigest()


def load_entry(ledger_dir: Path, index: int) -> dict:
    path = ledger_dir / f"{index}.yaml"
    with path.open("r", encoding="utf-8") as f:
        doc = yaml.safe_load(f)
    if not isinstance(doc, dict):
        raise ValueError(f"ledger/{index}.yaml: top-level is not a mapping")
    return doc


def mirror_to_sqlite(rows, db_path: Path) -> None:
    """SQLITE_MIRROR — local mirror only; ledger/*.yaml never rewritten."""
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS witness_rows ("
            " entry_index INTEGER PRIMARY KEY"
            ", event TEXT"
            ", regime TEXT"
            ", body_hash TEXT"
            ", declared_hash TEXT"
            ", verdict TEXT)"
        )
        conn.executemany(
            "INSERT OR REPLACE INTO witness_rows"
            " (entry_index, event, regime, body_hash, declared_hash, verdict)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            rows,
        )
        conn.commit()
    finally:
        conn.close()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Witness-chain triple mirror (Regime B)")
    parser.add_argument("--ledger", default="ledger", help="ledger directory")
    parser.add_argument("--db", default="pythonIDE/witness_chain_triple.sqlite",
                        help="local SQLite mirror path")
    args = parser.parse_args(argv)

    ledger_dir = Path(args.ledger)
    rows = []
    failures = 0

    for index in TRIPLE:
        try:
            doc = load_entry(ledger_dir, index)
        except Exception as exc:  # parse failure named, never hidden
            print(f"ledger/{index}.yaml: UNPARSEABLE — {exc}")
            rows.append((index, None, REGIME, None, None, "UNPARSEABLE"))
            failures += 1
            continue

        computed = body_hash(doc)
        declared = doc.get("hash")
        if declared is None:
            verdict = "NO_DECLARED_HASH"
        elif str(declared).strip().lower() == computed:
            verdict = "MATCH"
        else:
            verdict = "MISMATCH"
            failures += 1
        rows.append((index, str(doc.get("event", "")), REGIME, computed,
                    str(declared) if declared is not None else None, verdict))
        print(f"ledger/{index}.yaml: {verdict}  body_hash={computed[:16]}...")

    db_path = Path(args.db)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    mirror_to_sqlite(rows, db_path)
    print(f"mirror written: {db_path} ({len(rows)} rows, regime {REGIME})")

    if failures:
        print(f"witness triple: {failures} row(s) not verified")
        return 1
    print("witness triple 8337 → 8338 → 8339: verified against Regime B")
    return 0


if __name__ == "__main__":
    sys.exit(main())
