#!/usr/bin/env python3
"""
scripts/audit_sha3_backfill.py — read-only SHA3-256 ledger coverage audit.
NO_LEDGER_WRITE. One-time backfill = append NEW entry only (9237+).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from typing import Any, Dict, List, Optional, Tuple

DOMAIN = b"GARDEN.EVENT.v1\x00"
PHI2 = "2.618033988749895"
DELTA = "b^2-4ac"
THETA = "2.5416018462"

HASH_FIELDS = (
    "witness_prefix",
    "terminal_hex",
    "hash",
    "seal_hash",
    "verification_hash",
    "catalogue_sha3_256",
    "status_json_sha3_256",
    "agent_jsonl_sha3_256",
)


def _canonical_payload(n: int, event: str) -> str:
    return f"{n}|{event}|phi2={PHI2}|delta={DELTA}|theta={THETA}"


def _digest(payload: str) -> str:
    return hashlib.sha3_256(DOMAIN + payload.encode("ascii")).hexdigest()


def _git_show(branch: str, path: str) -> Optional[bytes]:
    try:
        out = subprocess.run(
            ["git", "show", f"{branch}:{path}"],
            capture_output=True,
            check=True,
        )
        return out.stdout
    except subprocess.CalledProcessError:
        return None


def _git_list(branch: str, pattern: str) -> List[str]:
    try:
        out = subprocess.run(
            ["git", "ls-tree", "-r", "--name-only", branch, "--", pattern],
            capture_output=True,
            check=True,
            text=True,
        )
        return [line for line in out.stdout.splitlines() if line.endswith(".yaml")]
    except subprocess.CalledProcessError:
        return []


def _load_yaml(raw: bytes) -> Optional[Dict[str, Any]]:
    try:
        import yaml
    except ImportError:
        print("pyyaml required", file=sys.stderr)
        sys.exit(2)
    try:
        data = yaml.safe_load(raw.decode("utf-8"))
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def _find_stored_hash(
    entry: Dict[str, Any],
) -> Tuple[Optional[str], Optional[str]]:
    for f in HASH_FIELDS:
        v = entry.get(f)
        if isinstance(v, str) and len(v) >= 16:
            if " · " in v:
                v = v.rsplit(" · ", 1)[-1]
            if all(c in "0123456789abcdefABCDEF" for c in v):
                return f, v.lower()
    seal = entry.get("seal")
    if isinstance(seal, str) and " · " in seal:
        tail = seal.rsplit(" · ", 1)[-1].strip()
        if len(tail) == 64 and all(c in "0123456789abcdefABCDEF" for c in tail):
            return "seal", tail.lower()
    return None, None


def audit_branch(branch: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for path in sorted(_git_list(branch, "ledger")):
        raw = _git_show(branch, path)
        if raw is None:
            continue
        entry = _load_yaml(raw)
        if not isinstance(entry, dict):
            rows.append({"branch": branch, "path": path, "status": "UNPARSEABLE"})
            continue
        n = entry.get("entry_index")
        event = entry.get("event")
        if not isinstance(n, int) or not isinstance(event, str):
            rows.append({"branch": branch, "path": path, "status": "NO_INDEX_OR_EVENT"})
            continue
        field, stored = _find_stored_hash(entry)
        recomputed = _digest(_canonical_payload(n, event))
        if stored is None:
            status = "MISSING"
        elif stored == recomputed:
            status = "MATCH"
        else:
            status = "MISMATCH"
        rows.append({
            "branch": branch, "path": path, "n": n, "event": event,
            "field": field, "stored": stored, "recomputed": recomputed,
            "status": status,
        })
    return rows


def _summary(rows: List[Dict[str, Any]]) -> Dict[str, int]:
    out = {"MATCH": 0, "MISSING": 0, "MISMATCH": 0, "UNPARSEABLE": 0, "NO_INDEX_OR_EVENT": 0}
    for r in rows:
        out[r["status"]] = out.get(r["status"], 0) + 1
    return out


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Read-only SHA3-256 ledger coverage audit.")
    ap.add_argument("--branches", default="main,deepseek,deepseek-ci")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--mismatches-only", action="store_true")
    args = ap.parse_args(argv)
    branches = [b.strip() for b in args.branches.split(",") if b.strip()]
    all_rows: List[Dict[str, Any]] = []
    for b in branches:
        all_rows.extend(audit_branch(b))
    if args.json:
        print(json.dumps({
            "branches": branches,
            "summary": _summary(all_rows),
            "rows": all_rows,
            "policy": "NO_LEDGER_WRITE",
            "backfill": "new entry only (9237+)",
        }, indent=2, sort_keys=True))
        return 0
    print("=" * 78)
    print("SHA3-256 COVERAGE AUDIT — READ-ONLY")
    print("=" * 78)
    print(f"branches = {branches}\n")
    for b in branches:
        rows = [r for r in all_rows if r["branch"] == b]
        s = _summary(rows)
        print(f"── {b} ──")
        print(
            f"   total={len(rows):4d}  MATCH={s.get('MATCH', 0):4d}  "
            f"MISSING={s.get('MISSING', 0):4d}  MISMATCH={s.get('MISMATCH', 0):4d}  "
            f"other={s.get('UNPARSEABLE', 0) + s.get('NO_INDEX_OR_EVENT', 0):4d}"
        )
        if args.mismatches_only:
            for r in rows:
                if r["status"] in ("MISMATCH", "MISSING"):
                    print(f"     {r['status']:9s}  {r.get('n', '?'):>6}  {r.get('event', '?')}")
        print()
    print("=" * 78)
    print("NO_LEDGER_WRITE — nothing was modified.")
    print("One-time backfill override: append NEW entry only; never rewrite YAML.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
