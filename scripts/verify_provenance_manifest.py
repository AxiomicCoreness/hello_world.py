#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
# SPDX-License-Identifier: MIT
"""Verify PROVENANCE_MANIFEST.json against the working tree.

Recomputes sha256 for every path listed in the manifest and compares to the
recorded digest. Also checks PROVENANCE_MANIFEST.sha256 against the manifest
file itself.

Exit codes:
  0 — all listed digests match and the sidecar digest matches
  1 — mismatch, missing file, or malformed manifest
  2 — usage / IO error

Note on staleness: the manifest is a snapshot of one commit. As main moves,
paths change and this script will (correctly) report mismatches. That is
expected. CI should not treat a stale-on-main mismatch as a gate failure for
unrelated PRs; the accompanying test only checks that this script runs and
that the manifest has a valid structure when present. Re-generate the
manifest when you intentionally refresh provenance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--root",
        type=Path,
        default=None,
        help="Repo root (default: parent of scripts/)",
    )
    args = ap.parse_args(argv)
    root = args.root or Path(__file__).resolve().parents[1]
    manifest_path = root / "PROVENANCE_MANIFEST.json"
    sidecar_path = root / "PROVENANCE_MANIFEST.sha256"

    if not manifest_path.is_file():
        print(f"MISSING manifest: {manifest_path}", file=sys.stderr)
        return 2

    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"MALFORMED manifest: {e}", file=sys.stderr)
        return 1

    required = ("repo", "base_commit", "author", "generated_at", "files")
    for k in required:
        if k not in data:
            print(f"MALFORMED: missing key {k!r}", file=sys.stderr)
            return 1
    if not isinstance(data["files"], list):
        print("MALFORMED: files must be a list", file=sys.stderr)
        return 1

    mismatches = 0
    missing = 0
    for entry in data["files"]:
        if not isinstance(entry, dict) or "path" not in entry or "sha256" not in entry:
            print(f"MALFORMED entry: {entry!r}", file=sys.stderr)
            mismatches += 1
            continue
        rel = entry["path"]
        expected = entry["sha256"]
        if not isinstance(expected, str) or len(expected) != 64:
            print(f"BAD DIGEST (want 64 hex): {rel} -> {expected!r}", file=sys.stderr)
            mismatches += 1
            continue
        path = root / rel
        if not path.is_file():
            print(f"MISSING {rel}", file=sys.stderr)
            missing += 1
            continue
        actual = sha256_file(path)
        if actual != expected:
            print(f"MISMATCH {rel}\n  expected {expected}\n  actual   {actual}", file=sys.stderr)
            mismatches += 1

    if sidecar_path.is_file():
        sidecar = sidecar_path.read_text(encoding="utf-8").strip().split()[0]
        actual_m = sha256_file(manifest_path)
        if sidecar != actual_m:
            print(
                f"SIDECAR MISMATCH PROVENANCE_MANIFEST.sha256\n"
                f"  expected {sidecar}\n  actual   {actual_m}",
                file=sys.stderr,
            )
            mismatches += 1
    else:
        print(f"MISSING sidecar: {sidecar_path}", file=sys.stderr)
        missing += 1

    total = mismatches + missing
    if total:
        print(
            f"FAIL: {mismatches} digest mismatch(es), {missing} missing; "
            f"{len(data['files'])} files listed",
            file=sys.stderr,
        )
        return 1

    print(
        f"OK: {len(data['files'])} files match; "
        f"manifest sha256={sha256_file(manifest_path)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
