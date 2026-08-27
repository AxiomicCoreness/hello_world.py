#!/usr/bin/env python3
"""Build untruncated SHA3-256 overlay for every ledger YAML.

Does not rewrite historical YAML. Mutating those files changes git blob SHAs
and invalidates the chain. The spine is the machine-readable fix.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import List, Tuple

DOMAIN = b"GARDEN.EVENT.v1"
HEX_LEN = 64
PHI2 = "2.618033988749895"
THETA = "2.5416018462"
GENESIS_PREV = "0" * HEX_LEN
DO_NOT_REWRITE = {
    "0336.yaml", "0403.yaml", "0404.yaml", "0515.yaml", "0516.yaml",
    "510510.yaml", "8338.yaml", "8530.yaml", "8532.yaml", "8535.yaml",
}


def digest(payload: str) -> str:
    hx = hashlib.sha3_256(DOMAIN + b"\x00" + payload.encode("utf-8")).hexdigest()
    if len(hx) != HEX_LEN:
        raise ValueError("truncated digest rejected")
    return hx


def index_of(name: str) -> str:
    m = re.match(r"^(\d+)", name)
    return m.group(1) if m else name


def list_yaml(ledger_dir: Path) -> List[Path]:
    files = [p for p in ledger_dir.glob("*.yaml") if p.name[0].isdigit()]
    files.sort(key=lambda p: (len(index_of(p.name)), index_of(p.name), p.name))
    return files


def build(ledger_dir: Path) -> Tuple[list, str]:
    rows = []
    prev = GENESIS_PREV
    for path in list_yaml(ledger_dir):
        idx = index_of(path.name)
        blob = hashlib.sha1(b"blob %d\0" % path.stat().st_size + path.read_bytes()).hexdigest()
        # Prefer recorded git blob when provided via sidecar; local sha1-git if cloned.
        payload = (
            f"{idx}|blob={blob}|prev={prev}|phi2={PHI2}|delta=b^2-4ac|theta={THETA}"
        )
        hx = digest(payload)
        rows.append({
            "entry_index": idx,
            "path": str(path.as_posix()),
            "git_blob_or_local": blob,
            "prev": prev,
            "event_hash": hx,
            "hex_len": HEX_LEN,
            "truncated": False,
            "rewritten_yaml": False,
            "do_not_rewrite": path.name in DO_NOT_REWRITE,
        })
        prev = hx
    return rows, prev


def main() -> None:
    root = Path(__file__).resolve().parent
    rows, tip = build(root)
    out = root / "hash_spine.jsonl"
    with out.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, separators=(",", ":")) + "\n")
    meta = {
        "count": len(rows),
        "tip": tip,
        "algo": "sha3-256",
        "hex_len": HEX_LEN,
        "truncated": False,
        "yaml_bodies_rewritten": False,
    }
    (root / "hash_spine_tip.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(meta))


if __name__ == "__main__":
    main()
