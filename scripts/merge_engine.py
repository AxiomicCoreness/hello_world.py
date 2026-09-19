#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""merge_engine.py — SHA3-256 manifest verifier. No ledger rewrite."""
from __future__ import annotations
import hashlib, json, subprocess, sys
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
try:
    import yaml
except ImportError:
    print("::error::PyYAML required", file=sys.stderr)
    sys.exit(2)
MANIFEST = Path("merge/manifest.yaml")
OUT_DIR = Path(".merge")
OUT_YAML = OUT_DIR / "merged_manifest.yaml"
OUT_JSON = OUT_DIR / "merged_report.json"
HASH_ALGO = "sha3_256"
@dataclass
class EntryResult:
    path: str
    role: str
    present: bool = False
    size: int = 0
    digest: str = ""
    head_digest: str = ""
    digest_matches_head: bool = False
    head_exists: bool = False
    ledger_index: int | None = None
    immutable: bool = False
    immutable_ok: bool = True
    yaml_ok: bool | None = None
    notes: list[str] = field(default_factory=list)
def sha3_file(p: Path) -> str:
    return hashlib.new(HASH_ALGO, p.read_bytes()).hexdigest()
def head_bytes(path: str) -> bytes | None:
    try:
        return subprocess.check_output(["git", "show", f"HEAD:{path}"], stderr=subprocess.DEVNULL)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
def verify_entry(e: dict) -> EntryResult:
    p = Path(e["path"])
    r = EntryResult(path=e["path"], role=e.get("role", "unknown"), immutable=bool(e.get("immutable", False)))
    if not p.is_file():
        r.notes.append("file not present on this ref")
        return r
    r.present = True
    r.size = p.stat().st_size
    r.digest = sha3_file(p)
    hb = head_bytes(e["path"])
    if hb is not None:
        r.head_exists = True
        r.head_digest = hashlib.new(HASH_ALGO, hb).hexdigest()
        r.digest_matches_head = r.digest == r.head_digest
    if r.immutable and r.head_exists and not r.digest_matches_head:
        r.immutable_ok = False
        r.notes.append("immutable file modified vs HEAD")
    if e.get("role") == "ledger":
        try:
            data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
            if not isinstance(data, dict):
                r.yaml_ok = False
            else:
                r.yaml_ok = True
                idx = data.get("entry_index")
                if isinstance(idx, int):
                    r.ledger_index = idx
        except yaml.YAMLError as ex:
            r.yaml_ok = False
            r.notes.append(str(ex))
    return r
def main() -> int:
    if not MANIFEST.exists():
        return 2
    entries = (yaml.safe_load(MANIFEST.read_text(encoding="utf-8")) or {}).get("entries") or []
    results = [verify_entry(e) for e in entries]
    by_index: dict[int, list[str]] = defaultdict(list)
    for r in results:
        if r.role == "ledger" and r.ledger_index is not None:
            by_index[r.ledger_index].append(r.path)
    conflicts = [{"entry_index": i, "paths": p} for i, p in sorted(by_index.items()) if len(p) > 1]
    immutable_violations = [r.path for r in results if r.immutable and not r.immutable_ok]
    missing = [r.path for r in results if not r.present]
    yaml_bad = [r.path for r in results if r.yaml_ok is False]
    OUT_DIR.mkdir(exist_ok=True)
    merged = {
        "generated_by": "merge-engine",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "hash_algo": HASH_ALGO,
        "counts": {"total": len(results), "present": sum(1 for r in results if r.present),
                   "missing": len(missing), "conflicts": len(conflicts),
                   "immutable_violations": len(immutable_violations), "yaml_errors": len(yaml_bad)},
        "conflicts": conflicts, "immutable_violations": immutable_violations,
        "yaml_errors": yaml_bad, "missing": missing, "entries": [asdict(r) for r in results],
    }
    OUT_YAML.write_text(yaml.dump(merged, sort_keys=False, allow_unicode=True), encoding="utf-8")
    OUT_JSON.write_text(json.dumps(merged, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print(f"entries verified: {len(results)} present={merged['counts']['present']} missing={merged['counts']['missing']}")
    return 1 if (conflicts or immutable_violations or yaml_bad) else 0
if __name__ == "__main__":
    sys.exit(main())
