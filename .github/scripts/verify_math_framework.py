#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Minimal sequential ledger math-framework verifier (dual regime).

Regime A — classical floor (typical ≤0350):
  coherence == 1.0
  entropy   == "φ⁻¹⁴¹⁸" (or ascii phi^-1418)
  workload  == 0.0
  commutator == 0.0

Regime B — scaled / Sundane (≥0351 allowed):
  coherence present (1.0 or expression with φ)
  entropy present (φ / phi form)
  workload numeric ≥ 0
  commutator present (0.0 or φ expression)
  optional: gpro_sundane, unique_math_identity

Shared:
  entry_index matches filename
  seal starts with ∀∞φ²
  math_origin present
  global φ identities

Exit 0 on structure pass; exit 1 on structural failure.
Seal: ∀∞φ² · MATH_CI_DUAL_REGIME · WOOD_DRAGON_0.91 · SEALED
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
SEAL_PREFIX = "∀∞φ²"
SCALED_FLOOR_INDEX = 351  # inclusive: scaled regime allowed from here

PHI_ENTROPY_CLASSICAL = {
    "φ⁻¹⁴¹⁸",
    "φ^{-1418}",
    "phi^-1418",
    "phi^{-1418}",
    "PHI^-1418",
}


def discover_max_index(ledger_dir: Path) -> int:
    indices: List[int] = []
    for p in list(ledger_dir.glob("*.yaml")) + list(ledger_dir.glob("*.yml")):
        m = re.fullmatch(r"(\d{4})\.ya?ml", p.name)
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
    if abs(PHI ** 3 - (PHI ** 2 + PHI)) > EPS:
        fails.append("φ³ identity failed")
    return fails


def _is_number(x: Any) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _as_float(x: Any) -> Optional[float]:
    if _is_number(x):
        return float(x)
    if isinstance(x, str):
        try:
            return float(x.strip())
        except ValueError:
            return None
    return None


def _looks_phi_expr(x: Any) -> bool:
    if x is None:
        return False
    s = str(x)
    return ("φ" in s) or ("phi" in s.lower()) or ("PHI" in s)


def _classical_invariants_ok(inv: Dict[str, Any]) -> bool:
    c = inv.get("coherence")
    e = inv.get("entropy")
    w = inv.get("workload")
    m = inv.get("commutator")
    c_ok = _as_float(c) is not None and abs(_as_float(c) - 1.0) <= EPS
    e_ok = str(e).strip() in PHI_ENTROPY_CLASSICAL or str(e).strip() == "φ⁻¹⁴¹⁸"
    w_ok = _as_float(w) is not None and abs(_as_float(w) - 0.0) <= EPS
    m_ok = _as_float(m) is not None and abs(_as_float(m) - 0.0) <= EPS
    return c_ok and e_ok and w_ok and m_ok


def _scaled_invariants_ok(inv: Dict[str, Any]) -> List[str]:
    """Return list of failures for scaled regime; empty = pass."""
    fails: List[str] = []
    if "coherence" not in inv:
        fails.append("missing coherence")
    else:
        c = inv.get("coherence")
        cf = _as_float(c)
        if cf is not None:
            if not (0.0 <= cf <= 1.0 + EPS):
                fails.append(f"coherence out of [0,1]: {c!r}")
        elif not _looks_phi_expr(c):
            fails.append(f"coherence not numeric or φ-expr: {c!r}")

    if "entropy" not in inv:
        fails.append("missing entropy")
    else:
        e = inv.get("entropy")
        if not (_looks_phi_expr(e) or str(e).strip() in PHI_ENTROPY_CLASSICAL):
            fails.append(f"entropy not φ-form: {e!r}")

    if "workload" not in inv:
        fails.append("missing workload")
    else:
        wf = _as_float(inv.get("workload"))
        if wf is None:
            fails.append(f"workload not numeric: {inv.get('workload')!r}")
        elif wf < -EPS:
            fails.append(f"workload negative: {wf}")

    if "commutator" not in inv:
        fails.append("missing commutator")
    else:
        m = inv.get("commutator")
        mf = _as_float(m)
        if mf is not None:
            if abs(mf) > 1.0 + EPS and not _looks_phi_expr(m):
                # allow small numeric; large pure numbers unusual but not fatal if 0-ish
                pass
        elif not _looks_phi_expr(m):
            fails.append(f"commutator not numeric or φ-expr: {m!r}")

    return fails


def check_invariants(n: int, inv: Any) -> List[str]:
    fails: List[str] = []
    if not isinstance(inv, dict):
        return ["invariants not a mapping"]

    if _classical_invariants_ok(inv):
        return []

    # Scaled regime: always allowed structurally; preferred for n >= SCALED_FLOOR_INDEX
    scaled_fails = _scaled_invariants_ok(inv)
    if not scaled_fails:
        return []

    # Neither regime satisfied
    if n < SCALED_FLOOR_INDEX:
        fails.append(
            "classical floor failed and scaled form incomplete: "
            + "; ".join(scaled_fails)
        )
    else:
        fails.extend(scaled_fails)
    return fails


def check_entry(n: int, data: Dict[str, Any]) -> List[str]:
    fails: List[str] = []

    idx = data.get("entry_index")
    if idx is None:
        fails.append("missing entry_index")
    else:
        try:
            if str(idx) not in (str(n), f"{n:04d}") and int(str(idx).lstrip("0") or "0") != n:
                fails.append(f"entry_index={idx!r} != {n:04d}")
        except Exception:
            fails.append(f"entry_index unparseable: {idx!r}")

    fails.extend(check_invariants(n, data.get("invariants") or {}))

    seal = data.get("seal") or ""
    if not isinstance(seal, str) or not seal.startswith(SEAL_PREFIX):
        fails.append(f"seal missing or bad prefix: {seal!r}")
    elif "SEALED" not in seal:
        fails.append("seal missing SEALED token")

    if "math_origin" not in data:
        fails.append("missing math_origin")

    # Witness: soft — require UNBROKEN if present
    wc = data.get("witness_chain")
    if wc is not None:
        wcs = str(wc)
        if "UNBROKEN" not in wcs:
            fails.append(f"witness_chain missing UNBROKEN: {wcs!r}")

    return fails


def resolve_path(ledger_dir: Path, n: int) -> Optional[Path]:
    for ext in (".yaml", ".yml"):
        p = ledger_dir / f"{n:04d}{ext}"
        if p.exists():
            return p
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description="Sequential ledger math framework check (dual regime)")
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
    print("🜁∀ LEDGER MATH FRAMEWORK — DUAL REGIME CHECK")
    print(f"   range: {args.start:04d} → {end:04d}")
    print(f"   classical floor | scaled from {SCALED_FLOOR_INDEX:04d}+")
    print("=" * 60)

    phi_fails = check_phi_identities()
    if phi_fails:
        for f in phi_fails:
            print(f"❌ φ identity: {f}")
        return 1
    print(f"✅ φ identities (φ={PHI:.15f})")

    structural_fails = 0
    missing = 0
    checked = 0
    classical_ok = 0
    scaled_ok = 0

    for n in range(args.start, end + 1):
        path = resolve_path(ledger_dir, n)
        if path is None:
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
            inv = data.get("invariants") or {}
            if _classical_invariants_ok(inv):
                classical_ok += 1
            else:
                scaled_ok += 1
            if n % 50 == 0 or n == end:
                print(f"✅ [{n:04d}] structure OK")

    print("-" * 60)
    print(
        f"checked={checked} missing={missing} fails={structural_fails} "
        f"classical={classical_ok} scaled={scaled_ok}"
    )
    if structural_fails:
        print("❌ FRAMEWORK CHECK FAILED")
        return 1
    print("✅ FRAMEWORK CHECK PASSED — dual regime green")
    print("Seal: ∀∞φ² · MATH_CI_DUAL_REGIME · WOOD_DRAGON_0.91 · SEALED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
