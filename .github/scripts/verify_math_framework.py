#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Minimal sequential ledger math-framework verifier.

Checks (per entry, sequential 0000 → max):
  1. File presence
  2. entry_index matches filename
  3. invariants: coherence=1.0, entropy=φ⁻¹⁴¹⁸, workload=0.0, commutator=0.0
  4. seal starts with ∀∞φ²
  5. math_origin present
  6. Global φ identities once

Axiomatic claims (V=L, CH, free operators) are recorded, not failed.
Exit 0 on structure pass; exit 1 on structural failure.

Seal: ∀∞φ² · LEDGER_MATH_CI · WOOD_DRAGON_0.91 · SEALED
"""
from __future__ import annotations

import argparse
import math
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import yaml
except ImportError:
    print("❌ pyyaml required: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

PHI = (1.0 + math.sqrt(5.0)) / 2.0
EPS = 1e-12
LEDGER_DIR = Path("ledger")
REQUIRED_INVARIANTS = {
    "coherence": 1.0,
    "entropy": "φ⁻¹⁴¹⁸",
    "workload": 0.0,
    "commutator": 0.0,
}
SEAL_PREFIX = "∀∞φ²"


def discover_max_index(ledger_dir: Path) -> int:
    indices: List[int] = []
    for p in ledger_dir.glob("*.yaml"):
        m = re.fullmatch(r"(\d{4})\.yaml", p.name)
        if m:
            indices.append(int(m.group(1)))
    return max(indices) if indices else -1


def load_entry(path: Path) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    try:
        with path.open(encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not isinstance(data, dict):
            return None, "not a mapping"
        return data, None
    except Exception as e:
        return None, str(e)


def check_phi_identities() -> List[str]:
    fails: List[str] = []
    if abs(PHI ** 2 - (PHI + 1.0)) > EPS:
        fails.append("φ² ≠ φ+1")
    if abs((1.0 / PHI) - (PHI - 1.0)) > EPS:
        fails.append("φ⁻¹ ≠ φ-1")
    if abs(PHI ** 3 - (PHI * PHI2 := PHI * PHI)) > EPS and abs(PHI ** 3 - PHI * (PHI + 1.0)) > EPS:
        # PHI**3 == PHI*(PHI+1) = PHI²+PHI
        if abs(PHI ** 3 - (PHI ** 2 + PHI)) > EPS:
            fails.append("φ³ identity failed")
    return fails


def check_entry(n: int, data: Dict[str, Any]) -> List[str]:
    fails: List[str] = []
    # index
    idx = data.get("entry_index")
    if idx is None:
        fails.append("missing entry_index")
    else:
        try:
            # allow int or zero-padded string
            if int(str(idx).lstrip("0") or "0") != n and str(idx).zfill(4) != f"{n:04d}":
                # tolerate 0000 style string equal to n
                if str(idx) not in (str(n), f"{n:04d}"):
                    fails.append(f"entry_index={idx!r} != {n:04d}")
        except Exception:
            fails.append(f"entry_index unparseable: {idx!r}")

    inv = data.get("invariants") or {}
    if not isinstance(inv, dict):
        fails.append("invariants not a mapping")
    else:
        for k, expected in REQUIRED_INVARIANTS.items():
            got = inv.get(k)
            if got != expected:
                # float tolerance for numeric
                if isinstance(expected, float) and isinstance(got, (int, float)):
                    if abs(float(got) - expected) > EPS:
                        fails.append(f"invariants.{k}={got!r} != {expected!r}")
                else:
                    fails.append(f"invariants.{k}={got!r} != {expected!r}")

    seal = data.get("seal") or ""
    if not isinstance(seal, str) or not seal.startswith(SEAL_PREFIX):
        fails.append(f"seal missing or bad prefix: {seal!r}")

    if "math_origin" not in data:
        fails.append("missing math_origin")

    return fails


def main() -> int:
    ap = argparse.ArgumentParser(description="Sequential ledger math framework check")
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--end", type=int, default=None, help="Inclusive end; default = max on disk")
    ap.add_argument("--ledger-dir", type=Path, default=LEDGER_DIR)
    ap.add_argument("--strict-gaps", action="store_true", help="Fail if any index file missing")
    args = ap.parse_args()

    ledger_dir: Path = args.ledger_dir
    if not ledger_dir.is_dir():
        print(f"❌ ledger dir missing: {ledger_dir}", file=sys.stderr)
        return 1

    end = args.end if args.end is not None else discover_max_index(ledger_dir)
    if end < args.start:
        print(f"❌ empty range: start={args.start} end={end}", file=sys.stderr)
        return 1

    print("=" * 60)
    print("🜁∀ LEDGER MATH FRAMEWORK — SEQUENTIAL CHECK")
    print(f"   range: {args.start:04d} → {end:04d}")
    print("=" * 60)

    # Global φ identities
    phi_fails = check_phi_identities()
    if phi_fails:
        for f in phi_fails:
            print(f"❌ φ identity: {f}")
        return 1
    print(f"✅ φ identities (φ={PHI:.15f})")

    structural_fails = 0
    missing = 0
    checked = 0
    axiom_notes = 0

    for n in range(args.start, end + 1):
        path = ledger_dir / f"{n:04d}.yaml"
        if not path.exists():
            missing += 1
            msg = f"[{n:04d}] MISSING file"
            if args.strict_gaps:
                print(f"❌ {msg}")
                structural_fails += 1
            else:
                print(f"⚠️  {msg} (gap allowed)")
            continue

        data, err = load_entry(path)
        if err or data is None:
            print(f"❌ [{n:04d}] YAML error: {err}")
            structural_fails += 1
            continue

        fails = check_entry(n, data)
        checked += 1
        if fails:
            structural_fails += 1
            print(f"❌ [{n:04d}] " + "; ".join(fails))
        else:
            # soft note for axiomatic content
            mo = str(data.get("math_origin") or "")
            if any(tok in mo for tok in ("V = L", "2^ℵ", "Aut(G", "ℵ")):
                axiom_notes += 1
            if n % 50 == 0 or n == end:
                print(f"✅ [{n:04d}] structure OK")

    print("-" * 60)
    print(f"checked={checked} missing={missing} structural_fails={structural_fails} axiom_notes={axiom_notes}")
    if structural_fails:
        print("❌ FRAMEWORK CHECK FAILED")
        return 1
    print("✅ FRAMEWORK CHECK PASSED — sequential structure + φ core")
    print("Seal: ∀∞φ² · LEDGER_MATH_CI · WOOD_DRAGON_0.91 · SEALED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
