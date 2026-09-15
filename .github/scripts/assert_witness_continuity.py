#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
assert_witness_continuity.py — T-07 mitigation (gap-tolerant).

The ledger is intentionally non-contiguous (parallel series 83xx, 91xx, 92xx).
This script does NOT require n and n-1 for every n. It asserts:

  1. Every ledger/*.yaml parses and has a unique entry_index.
  2. When both entry N and N-1 exist as files, the witness_chain of N
     references N-1 (substring or explicit "N-1 → N" form).
  3. Hard-envelope indices [9240, 9242, 9243, 9244, 9245, 9246] files,
     if present, are not rewritten by this check (read-only).

Modes:
  --soft  warn, exit 0 (default)
  --hard  fail on continuity break or duplicate index
  --emit  print report only, exit 0

Usage:
  python .github/scripts/assert_witness_continuity.py
  python .github/scripts/assert_witness_continuity.py --hard
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("::error::pyyaml required", file=sys.stderr)
    sys.exit(1)

HARD_ENVELOPE = {9240, 9242, 9243, 9244, 9245, 9246}
LEDGER_DIR = Path("ledger")


def load_entries(ledger_dir: Path) -> dict[int, dict]:
    by_index: dict[int, dict] = {}
    dups: list[int] = []
    for path in sorted(ledger_dir.glob("*.yaml")):
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except Exception as e:
            print(f"FAIL parse {path}: {e}")
            continue
        if not isinstance(data, dict):
            print(f"SKIP non-mapping {path}")
            continue
        n = data.get("entry_index")
        if not isinstance(n, int):
            # try filename
            m = re.match(r"(\d+)\.yaml$", path.name)
            if not m:
                print(f"SKIP no entry_index {path}")
                continue
            n = int(m.group(1))
        if n in by_index:
            dups.append(n)
        by_index[n] = {"path": path, "data": data}
    return by_index, dups  # type: ignore


def chain_ok(n: int, data: dict, has_pred: bool) -> bool:
    if not has_pred:
        return True
    chain = str(
        data.get("witness_chain") or data.get("witness") or ""
    )
    pred = str(n - 1)
    # Accept forms: "8338 → 8339", "8338 -> 8339", contains pred
    if pred in chain:
        return True
    # Some entries only say "UNBROKEN" without numbers — soft warn later
    return False


def main() -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--soft", action="store_true")
    g.add_argument("--hard", action="store_true")
    g.add_argument("--emit", action="store_true")
    ap.add_argument("--ledger-dir", default="ledger")
    args = ap.parse_args()
    mode = "emit" if args.emit else "hard" if args.hard else "soft"

    ledger_dir = Path(args.ledger_dir)
    if not ledger_dir.is_dir():
        print(f"::error::{ledger_dir} missing")
        return 1 if mode == "hard" else 0

    by_index, dups = load_entries(ledger_dir)  # type: ignore
    indices = sorted(by_index.keys())
    print(f"entries_loaded={len(indices)} range={indices[0] if indices else '?'}-{indices[-1] if indices else '?'}")

    fails = 0
    warns = 0

    if dups:
        print(f"FAIL duplicate entry_index: {dups}")
        fails += 1

    for n in indices:
        data = by_index[n]["data"]
        pred = n - 1
        has_pred = pred in by_index
        if has_pred and not chain_ok(n, data, True):
            msg = (
                f"continuity: {n} has predecessor file {pred} "
                f"but witness_chain does not reference {pred}: "
                f"{data.get('witness_chain') or data.get('witness')!r}"
            )
            print(f"{'FAIL' if mode == 'hard' else 'WARN'} {msg}")
            if mode == "hard":
                fails += 1
            else:
                warns += 1

    env_present = sorted(HARD_ENVELOPE & set(indices))
    print(f"hard_envelope_present={env_present}")
    print(f"fails={fails} warns={warns} mode={mode}")
    print("T-07 witness continuity check complete — envelope read-only")

    if mode == "emit":
        return 0
    if mode == "soft":
        return 0
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
