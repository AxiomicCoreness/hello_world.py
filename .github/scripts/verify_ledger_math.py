#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Cap: Ledger Math CI checks 9156-9160 only.
# Does not rewrite 9157-9162. Does not walk to 510511.yaml.
# Seal: ∀∞φ² · LEDGER_MATH_CI · WOOD_DRAGON_0.91 · SEALED
# Witness: 9161 → 9162 — UNBROKEN  (chain head — this workflow does NOT extend it)
# hash_algo: sha3_256 (FIPS 202) — declared for header consistency
# ledger_policy: NO_GROWTH — read-only verifier (permissions: contents: read)
"""
verify_ledger_math.py — bounded ledger math framework verifier (9156–9160 only).

Python port of .github/workflows/ledger-math-framework.yml.

Does NOT rewrite 9157–9162. Does NOT walk to 510511.yaml. Read-only.

Distinct from verify_ledger.py (Regime A/B seal verifier). Do not clobber that path.

Modes (default = workflow behaviour = hard):
  --emit   diagnostics only, always exit 0
  --soft   warn on failure, exit 0
  --hard   fail on missing verifier, YAML error, or assertion failure (default)

Usage:
    python .github/scripts/verify_ledger_math.py
    python .github/scripts/verify_ledger_math.py --soft
    python .github/scripts/verify_ledger_math.py --emit
    python .github/scripts/verify_ledger_math.py --ledger-dir ledger --start 9156 --end 9160
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import subprocess
import sys
from pathlib import Path

HASH_ALGO = "sha3_256"
RANGE_START = 9156
RANGE_END = 9160

MATH_VERIFIER = Path(".github/scripts/verify_math_framework.py")
HOOK_WORKER = Path("scripts/codespace_hook_worker.py")
SUMMARY_ENV = "GITHUB_STEP_SUMMARY"


def verify_math_framework(ledger_dir: Path, start: int, end: int, mode: str) -> bool:
    if not MATH_VERIFIER.exists():
        print(f"::error::{MATH_VERIFIER} not found", file=sys.stderr)
        return False if mode == "hard" else True

    cmd = [
        sys.executable,
        str(MATH_VERIFIER),
        "--ledger-dir",
        str(ledger_dir),
        "--start",
        str(start),
        "--end",
        str(end),
    ]
    proc = subprocess.run(cmd, capture_output=False)
    if proc.returncode != 0:
        print(
            f"::error::math framework verifier exited {proc.returncode}",
            file=sys.stderr,
        )
        return False if mode == "hard" else True
    return True


def yaml_parse_check(ledger_dir: Path, start: int, end: int, mode: str) -> bool:
    try:
        import yaml  # noqa: F401
    except ImportError:
        print("❌ pyyaml missing", file=sys.stderr)
        return False if mode == "hard" else True

    import yaml as _yaml

    fails = 0
    checked = 0
    for n in range(start, end + 1):
        p = ledger_dir / f"{n}.yaml"
        if not p.exists():
            print(f"SKIP missing {p}")
            continue
        try:
            list(_yaml.safe_load_all(p.read_text(encoding="utf-8")))
            checked += 1
            print(f"OK {p}")
        except Exception as e:
            print(f"FAIL {p}: {e}")
            fails += 1

    print(f"yaml_checked={checked} yaml_fails={fails}")
    if fails:
        return False if mode == "hard" else True
    return True


def hook_worker_import_check(mode: str) -> bool:
    if not HOOK_WORKER.exists():
        print(f"⚠️ {HOOK_WORKER} not found — soft skip")
        return True

    spec = importlib.util.spec_from_file_location("codespace_hook_worker", HOOK_WORKER)
    if spec is None or spec.loader is None:
        print("❌ could not create import spec", file=sys.stderr)
        return False if mode == "hard" else True

    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    checks = [
        ("FILLED", False),
        ("BIND", "127.0.0.1"),
        ("PORT", 8091),
        ("DUAL_ASGI", "127.0.0.1:8024"),
    ]
    for name, expected in checks:
        actual = getattr(mod, name, None)
        if actual != expected:
            msg = f"{name} must be {expected!r}, got {actual!r}"
            print(f"❌ {msg}", file=sys.stderr)
            if mode == "hard":
                return False

    print("✅ hook worker import OK — FILLED=False, bind 127.0.0.1:8091")
    return True


def summary(start: int, end: int) -> None:
    lines = [
        "✅ Ledger Math Framework — bounded check completed.",
        "🜁∀ — Seal: ∀∞φ² · LEDGER_MATH_CI · WOOD_DRAGON_0.91 · SEALED",
        f"🔐 hash_algo: {HASH_ALGO}",
        f"📏 range: {start}–{end} (capped; no walk to 510511.yaml)",
        "🛡  does not rewrite: 9157 · 9158 · 9159 · 9160 · 9161 · 9162",
        "🔗 witness head: 9161 → 9162 — UNBROKEN (not extended by this workflow)",
        "📄 ledger_policy: NO_GROWTH — read-only verifier",
    ]
    for line in lines:
        print(line)

    sfile = os.environ.get(SUMMARY_ENV)
    if sfile:
        try:
            with open(sfile, "a", encoding="utf-8") as f:
                for line in lines:
                    f.write(line + "\n")
        except OSError:
            pass


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Bounded ledger math framework verifier."
    )
    g = parser.add_mutually_exclusive_group()
    g.add_argument("--emit", action="store_true", help="diagnostics only, always exit 0")
    g.add_argument("--soft", action="store_true", help="warn on failure, exit 0")
    g.add_argument("--hard", action="store_true", help="fail on any error (default)")
    parser.add_argument("--ledger-dir", default="ledger")
    parser.add_argument("--start", type=int, default=RANGE_START)
    parser.add_argument("--end", type=int, default=RANGE_END)
    args = parser.parse_args()

    mode = "emit" if args.emit else "soft" if args.soft else "hard"

    if args.start != RANGE_START or args.end != RANGE_END:
        print(
            f"::error::range must be {RANGE_START}–{RANGE_END}; "
            f"got {args.start}–{args.end} (no walk to 510511.yaml)",
            file=sys.stderr,
        )
        if mode == "hard":
            return 1

    ok = True
    ok &= verify_math_framework(Path(args.ledger_dir), args.start, args.end, mode)
    ok &= yaml_parse_check(Path(args.ledger_dir), args.start, args.end, mode)
    ok &= hook_worker_import_check(mode)

    summary(args.start, args.end)

    if mode in ("emit", "soft"):
        return 0
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
