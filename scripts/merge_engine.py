#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
merge_engine.py — SHA3-256 manifest verifier + discoverable Merkle root.

Reads  merge/manifest.yaml
Writes .merge/merged_manifest.yaml
       .merge/merged_report.json
       .merge/merkle_root.json   (Node-discoverable)

Verification:
  - every present file: SHA3-256 of on-disk bytes
  - role=ledger: YAML parse; capture entry_index when present
  - immutable=true + expected_sha3_256: on-disk digest must match recorded
  - immutable=true without expected_sha3_256 + HEAD present: still compare HEAD
  - conflicts when two entries share a ledger index
  - missing files reported (not fatal)

Merkle:
  leaves = SHA3-256(path + NUL + digest) for present entries, sorted by path
  internal = SHA3-256(left || right); odd last leaf promoted
  root written to report and .merge/merkle_root.json

Does NOT rewrite ledger bodies. Does NOT invent seals.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    print("::error::PyYAML required: pip install pyyaml", file=sys.stderr)
    sys.exit(2)

MANIFEST = Path("merge/manifest.yaml")
OUT_DIR = Path(".merge")
OUT_YAML = OUT_DIR / "merged_manifest.yaml"
OUT_JSON = OUT_DIR / "merged_report.json"
OUT_MERKLE = OUT_DIR / "merkle_root.json"
HASH_ALGO = "sha3_256"


@dataclass
class EntryResult:
    path: str
    role: str
    present: bool = False
    size: int = 0
    digest: str = ""
    expected_sha3_256: str = ""
    head_digest: str = ""
    digest_matches_head: bool = False
    head_exists: bool = False
    ledger_index: int | None = None
    immutable: bool = False
    immutable_ok: bool = True
    yaml_ok: bool | None = None
    notes: list[str] = field(default_factory=list)


def sha3_bytes(data: bytes) -> str:
    return hashlib.new(HASH_ALGO, data).hexdigest()


def sha3_file(p: Path) -> str:
    return sha3_bytes(p.read_bytes())


def head_bytes(path: str) -> bytes | None:
    try:
        return subprocess.check_output(
            ["git", "show", f"HEAD:{path}"],
            stderr=subprocess.DEVNULL,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def merkle_root(leaves: list[str]) -> str:
    """Binary Merkle over leaf hex strings (each re-hashed as ASCII for stability)."""
    if not leaves:
        return sha3_bytes(b"")
    level = [hashlib.new(HASH_ALGO, h.encode("ascii")).digest() for h in leaves]
    while len(level) > 1:
        nxt: list[bytes] = []
        for i in range(0, len(level), 2):
            if i + 1 < len(level):
                nxt.append(hashlib.new(HASH_ALGO, level[i] + level[i + 1]).digest())
            else:
                nxt.append(level[i])  # promote odd last
        level = nxt
    return level[0].hex()


def leaf_digest(path: str, file_digest: str) -> str:
    return sha3_bytes(f"{path}\0{file_digest}".encode("utf-8"))


def verify_entry(e: dict) -> EntryResult:
    p = Path(e["path"])
    expected = (e.get("expected_sha3_256") or "").strip().lower()
    r = EntryResult(
        path=e["path"],
        role=e.get("role", "unknown"),
        immutable=bool(e.get("immutable", False)),
        expected_sha3_256=expected,
    )

    if not p.is_file():
        r.notes.append("file not present on this ref")
        return r

    r.present = True
    r.size = p.stat().st_size
    r.digest = sha3_file(p)

    hb = head_bytes(e["path"])
    if hb is not None:
        r.head_exists = True
        r.head_digest = sha3_bytes(hb)
        r.digest_matches_head = r.digest == r.head_digest

    # Primary immutability: recorded expected_sha3_256 (seal-time reference)
    if r.immutable and expected:
        if r.digest != expected:
            r.immutable_ok = False
            r.notes.append("immutable file differs from recorded expected_sha3_256")
    elif r.immutable and r.head_exists and not r.digest_matches_head:
        # Fallback when expected not yet populated
        r.immutable_ok = False
        r.notes.append("immutable file modified vs HEAD (no expected_sha3_256)")

    if e.get("role") == "ledger":
        try:
            data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
            if not isinstance(data, dict):
                r.yaml_ok = False
                r.notes.append(f"top-level is {type(data).__name__}, not mapping")
            else:
                r.yaml_ok = True
                idx = data.get("entry_index")
                if isinstance(idx, int):
                    r.ledger_index = idx
        except yaml.YAMLError as ex:
            r.yaml_ok = False
            r.notes.append(f"yaml parse error: {ex}")

    return r


def detect_conflicts(results: list[EntryResult]) -> list[dict]:
    by_index: dict[int, list[str]] = defaultdict(list)
    for r in results:
        if r.role == "ledger" and r.ledger_index is not None:
            by_index[r.ledger_index].append(r.path)
    return [
        {"entry_index": i, "paths": paths}
        for i, paths in sorted(by_index.items())
        if len(paths) > 1
    ]


def group_by_role(results: list[EntryResult]) -> dict[str, list[str]]:
    g: dict[str, list[str]] = defaultdict(list)
    for r in results:
        g[r.role].append(r.path)
    return {k: sorted(v) for k, v in sorted(g.items())}


def build_merkle(results: list[EntryResult]) -> dict[str, Any]:
    present = sorted(
        (r for r in results if r.present and r.digest),
        key=lambda r: r.path,
    )
    leaves = [leaf_digest(r.path, r.digest) for r in present]
    root = merkle_root(leaves)
    return {
        "algo": HASH_ALGO,
        "leaf_count": len(leaves),
        "leaf_formula": "SHA3-256(path + NUL + file_digest)",
        "node_formula": "SHA3-256(left || right); odd last promoted",
        "merkle_root": root,
        "leaves": [
            {"path": r.path, "file_digest": r.digest, "leaf": leaves[i]}
            for i, r in enumerate(present)
        ],
    }


def main() -> int:
    if not MANIFEST.exists():
        print(f"::error::{MANIFEST} not found", file=sys.stderr)
        return 2

    manifest = yaml.safe_load(MANIFEST.read_text(encoding="utf-8")) or {}
    entries = manifest.get("entries") or []
    if not entries:
        print("::error::manifest has no entries", file=sys.stderr)
        return 2

    results = [verify_entry(e) for e in entries]
    conflicts = detect_conflicts(results)
    groups = group_by_role(results)
    immutable_violations = [
        r.path for r in results if r.immutable and not r.immutable_ok
    ]
    missing = [r.path for r in results if not r.present]
    yaml_bad = [r.path for r in results if r.yaml_ok is False]
    merkle = build_merkle(results)

    OUT_DIR.mkdir(exist_ok=True)

    merged: dict[str, Any] = {
        "generated_by": "merge-engine",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "hash_algo": HASH_ALGO,
        "merkle_root": merkle["merkle_root"],
        "merkle": merkle,
        "counts": {
            "total": len(results),
            "present": sum(1 for r in results if r.present),
            "missing": len(missing),
            "conflicts": len(conflicts),
            "immutable_violations": len(immutable_violations),
            "yaml_errors": len(yaml_bad),
        },
        "groups": groups,
        "conflicts": conflicts,
        "immutable_violations": immutable_violations,
        "yaml_errors": yaml_bad,
        "missing": missing,
        "entries": [asdict(r) for r in results],
    }

    OUT_YAML.write_text(
        yaml.dump(merged, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    OUT_JSON.write_text(
        json.dumps(merged, indent=2, sort_keys=True, default=str),
        encoding="utf-8",
    )
    OUT_MERKLE.write_text(
        json.dumps(
            {
                "algo": HASH_ALGO,
                "merkle_root": merkle["merkle_root"],
                "leaf_count": merkle["leaf_count"],
                "leaf_formula": merkle["leaf_formula"],
                "node_formula": merkle["node_formula"],
                "generated_at": merged["generated_at"],
                "discoverable": True,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    print(f"entries verified: {len(results)}")
    print(f"  present: {merged['counts']['present']}")
    print(f"  missing: {merged['counts']['missing']}")
    print(f"  conflicts: {merged['counts']['conflicts']}")
    print(f"  immutable violations: {merged['counts']['immutable_violations']}")
    print(f"  yaml errors: {merged['counts']['yaml_errors']}")
    print(f"  merkle_root: {merkle['merkle_root']}")
    print(f"  written: {OUT_YAML}, {OUT_JSON}, {OUT_MERKLE}")

    hard_fail = bool(conflicts) or bool(immutable_violations) or bool(yaml_bad)
    return 1 if hard_fail else 0


if __name__ == "__main__":
    sys.exit(main())
