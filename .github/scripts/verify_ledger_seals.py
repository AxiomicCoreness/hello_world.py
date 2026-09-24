#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify_ledger_seals.py — ledger seal verifier for the Garden CI lane.

Contract (as documented in .github/workflows/ledger-seal-gate.yml):
    exit 0  — all seals verified, all --require entries present
    exit 1  — at least one mismatch OR a required entry is missing
    exit 2  — no ledger directory found at the given root

Seal conventions understood:
    1. `seal:` field ends with `· <64-hex>` (SHA3-256 over canonical JSON)
    2. `seal_sha3_256:` field containing a full 64-hex digest
    3. `hash:` / `sha3_256:` / `hash_sha3_256:` fields with a 64-hex digest

The verifier does not rewrite anything. It reads, computes, compares.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Iterable, Optional

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is required. Install with: pip install pyyaml", file=sys.stderr)
    sys.exit(2)


HEX64 = re.compile(r"[0-9a-f]{64}")
SEAL_TAIL = re.compile(r"·\s*([0-9a-f]{64})\s*$")


def canonical_json(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def extract_declared_digest(doc: dict) -> Optional[tuple[str, str]]:
    """
    Return (field_name, digest) if the document declares a 64-hex digest
    anywhere we know how to read. Return None otherwise.
    """
    for field in ("seal_sha3_256", "sha3_256", "hash_sha3_256"):
        v = doc.get(field)
        if isinstance(v, str) and HEX64.fullmatch(v.strip()):
            return field, v.strip()

    seal = doc.get("seal")
    if isinstance(seal, str):
        m = SEAL_TAIL.search(seal)
        if m:
            return "seal", m.group(1)
        # also accept a 64-hex anywhere in the seal string
        m2 = HEX64.search(seal)
        if m2:
            return "seal", m2.group(0)

    h = doc.get("hash")
    if isinstance(h, str) and HEX64.fullmatch(h.strip()):
        return "hash", h.strip()

    return None


def expected_digest(doc: dict) -> str:
    """
    Compute the expected digest over the document with the digest-bearing
    fields removed, so the digest does not depend on itself.
    """
    body = {k: v for k, v in doc.items() if k not in {
        "seal", "seal_sha3_256", "sha3_256", "hash_sha3_256", "hash"
    }}
    return hashlib.sha3_256(canonical_json(body).encode("utf-8")).hexdigest()


def check_file(path: Path) -> tuple[bool, str]:
    try:
        with path.open("r", encoding="utf-8") as f:
            doc = yaml.safe_load(f)
    except Exception as e:
        return False, f"{path}: YAML parse error: {e}"

    if not isinstance(doc, dict):
        return False, f"{path}: top-level not a mapping"

    declared = extract_declared_digest(doc)
    if declared is None:
        return True, f"{path}: no declared digest (skipped, informational)"

    field, digest = declared
    expected = expected_digest(doc)

    if digest == expected:
        return True, f"{path}: {field} OK  {digest[:16]}…"
    else:
        return False, (
            f"{path}: {field} MISMATCH\n"
            f"    declared: {digest}\n"
            f"    expected: {expected}"
        )


def find_entries(root: Path) -> list[Path]:
    return sorted(root.rglob("*.yaml"))


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Verify ledger seal digests.")
    ap.add_argument("root", help="repository root or ledger directory")
    ap.add_argument("--require", action="append", default=[],
                    help="entry index that must be present (e.g. --require 8958)")
    args = ap.parse_args(argv)

    root = Path(args.root).resolve()

    # locate ledger directory
    candidates = [root / "ledger", root]
    ledger_dir = next((c for c in candidates if c.is_dir()), None)
    if ledger_dir is None:
        print(f"ERROR: no ledger directory under {root}", file=sys.stderr)
        return 2

    entries = find_entries(ledger_dir)
    if not entries:
        print(f"ERROR: no YAML entries under {ledger_dir}", file=sys.stderr)
        return 2

    present_indices: set[str] = set()
    for p in entries:
        stem = p.stem
        # ledger/8958.yaml -> "8958"
        if stem.isdigit():
            present_indices.add(stem)

    # required entries
    missing_required = [r for r in args.require if r not in present_indices]

    # verify each
    ok_count = 0
    skipped = 0
    bad: list[str] = []

    for p in entries:
        ok, msg = check_file(p)
        if ok:
            if "skipped" in msg:
                skipped += 1
            else:
                ok_count += 1
            print(f"  ✓ {msg}")
        else:
            bad.append(msg)
            print(f"  ✗ {msg}", file=sys.stderr)

    print()
    print(f"  entries scanned : {len(entries)}")
    print(f"  verified OK     : {ok_count}")
    print(f"  skipped (no seal): {skipped}")
    print(f"  mismatches      : {len(bad)}")
    if args.require:
        print(f"  required present : {len(args.require) - len(missing_required)}/{len(args.require)}")

    if missing_required:
        print()
        print(f"  MISSING required entries: {', '.join(missing_required)}", file=sys.stderr)
        return 1

    if bad:
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
