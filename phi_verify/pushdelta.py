"""
Append-only file-write ledger.

Every file the kernel writes passes through push(). Each write is a
delta: a record chained to its predecessor by digest, exactly like the
main ledger. No file is written in place without a delta entry.

Ledger format: JSONL, one record per line, at pushdelta.ledger.jsonl
Record fields:
    path     — target file (relative to CWD)
    prev     — digest of previous delta ("0"*64 for genesis)
    digest   — sha3_256 of this file's content
    size     — byte count
    ts       — unix timestamp
"""
import hashlib
import json
import time
from pathlib import Path
from typing import Optional

LEDGER_PATH = Path("pushdelta.ledger.jsonl")


def _hash(b: bytes) -> str:
    return hashlib.sha3_256(b).hexdigest()


def read_head(ledger: Path = LEDGER_PATH) -> str:
    if not ledger.exists():
        return "0" * 64
    last = None
    with ledger.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                last = line
    if last is None:
        return "0" * 64
    return json.loads(last)["digest"]


def push(path: Path, content: bytes,
         ledger: Path = LEDGER_PATH) -> dict:
    """
    Write content to path and append a delta to the ledger.
    Returns the delta record.
    """
    path = Path(path)
    prev = read_head(ledger)
    digest = _hash(content)
    record = {
        "path": str(path),
        "prev": prev,
        "digest": digest,
        "size": len(content),
        "ts": time.time(),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    with ledger.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, sort_keys=True,
                           separators=(",", ":")) + "\n")
    return record


def verify_chain(ledger: Path = LEDGER_PATH) -> bool:
    """Every delta's prev must equal the previous delta's digest."""
    if not ledger.exists():
        return True
    prev = "0" * 64
    with ledger.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            if rec["prev"] != prev:
                return False
            prev = rec["digest"]
    return True
