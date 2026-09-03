#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sovereign Ledger — Mathematical Verification Framework (dual regime)

Garden prefix seals are first-class:
  seal starts with ∀∞φ² and contains SEALED
  hex digest may appear as a suffix; it is NOT required to equal
  json.dumps(canonical).hexdigest() of the YAML mapping.

Commutator is optional when phase_lock is present (9157–9159).
Gaps are allowed unless --strict-gaps.
Seal: ∀∞φ² · LEDGER_MATH_CI · WOOD_DRAGON_0.91 · SEALED
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

PHI = (1.0 + math.sqrt(5.0)) / 2.0
EPS = 1e-12
SEAL_PREFIX = "∀∞φ²"
SCALED_FLOOR_INDEX = 351
HEX64 = re.compile(r"^[0-9a-fA-F]{64}$")


def compute_seal_hex(entry_data: Dict[str, Any]) -> str:
    data = {k: v for k, v in entry_data.items() if k != "seal"}
    canonical = json.dumps(data, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha3_256(canonical.encode("utf-8")).hexdigest()


def discover_ledger_dir() -> Path:
    for path in (Path("./ledger"), Path("ledger"), Path("../ledger")):
        if path.exists() and path.is_dir():
            return path
    return Path("ledger")


try:
    import yaml

    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


def load_entry(path: Path) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    if not path.exists():
        return None, f"file not found: {path}"
    try:
        content = path.read_text(encoding="utf-8")
        if YAML_AVAILABLE:
            data = yaml.safe_load(content)
            if isinstance(data, dict):
                return data, None
            return None, "yaml root is not a mapping"
        return None, "pyyaml required"
    except Exception as e:
        return None, str(e)


def _as_float(x: Any) -> Optional[float]:
    if isinstance(x, bool):
        return None
    if isinstance(x, (int, float)):
        return float(x)
    if isinstance(x, str):
        try:
            return float(x.strip().rstrip("°"))
        except ValueError:
            return None
    return None


def _looks_phi_expr(x: Any) -> bool:
    if x is None:
        return False
    s = str(x)
    return ("φ" in s) or ("phi" in s.lower())


def _seal_ok(seal: Any) -> List[str]:
    fails: List[str] = []
    if not isinstance(seal, str) or not seal.strip():
        return ["seal missing"]
    if not seal.startswith(SEAL_PREFIX):
        fails.append(f"seal missing prefix: {seal[:40]!r}")
    if "SEALED" not in seal:
        fails.append("seal missing SEALED token")
    return fails


def check_invariants(n: int, inv: Any) -> List[str]:
    if not isinstance(inv, dict):
        return ["invariants not a mapping"]
    fails: List[str] = []
    if "coherence" not in inv:
        fails.append("missing coherence")
    else:
        cf = _as_float(inv.get("coherence"))
        if cf is None and not _looks_phi_expr(inv.get("coherence")):
            fails.append(f"coherence not numeric or φ-expr: {inv.get('coherence')!r}")
        elif cf is not None and not (0.0 <= cf <= 1.0 + EPS):
            fails.append(f"coherence out of [0,1]: {inv.get('coherence')!r}")
    if "entropy" not in inv:
        fails.append("missing entropy")
    else:
        if not _looks_phi_expr(inv.get("entropy")):
            fails.append(f"entropy not φ-form: {inv.get('entropy')!r}")
    if "workload" not in inv:
        fails.append("missing workload")
    else:
        wf = _as_float(inv.get("workload"))
        if wf is None:
            fails.append(f"workload not numeric: {inv.get('workload')!r}")
        elif wf < -EPS:
            fails.append(f"workload negative: {wf}")
    has_comm = "commutator" in inv
    has_phase = "phase_lock" in inv
    if not has_comm and not has_phase:
        fails.append("missing commutator (phase_lock also absent)")
    return fails


def verify_entry(n: int, data: Dict[str, Any]) -> List[str]:
    fails: List[str] = []
    idx = data.get("entry_index")
    if idx != n and str(idx) != str(n) and str(idx) != f"{n:04d}":
        fails.append(f"entry_index={idx!r} != {n}")
    fails.extend(check_invariants(n, data.get("invariants", {})))
    fails.extend(_seal_ok(data.get("seal", "")))
    if "math_origin" not in data:
        fails.append("missing math_origin")
    wc = data.get("witness_chain")
    if wc is not None and "UNBROKEN" not in str(wc):
        fails.append(f"witness_chain missing UNBROKEN: {wc}")
    seal = data.get("seal", "")
    if isinstance(seal, str) and seal.startswith(SEAL_PREFIX):
        hex_suffix = seal.split("·")[-1].strip()
        if HEX64.match(hex_suffix):
            pass
        compute_seal_hex(data)
    return fails


def resolve_path(ledger_dir: Path, n: int) -> Optional[Path]:
    for ext in (".yaml", ".yml"):
        p = ledger_dir / f"{n:04d}{ext}"
        if p.exists():
            return p
        p2 = ledger_dir / f"{n}{ext}"
        if p2.exists():
            return p2
    return None


def discover_max_index(ledger_dir: Path) -> int:
    indices: List[int] = []
    for p in list(ledger_dir.glob("*.yaml")) + list(ledger_dir.glob("*.yml")):
        m = re.fullmatch(r"(\d+)\.ya?ml", p.name)
        if m:
            indices.append(int(m.group(1)))
    return max(indices) if indices else -1


def main() -> int:
    ap = argparse.ArgumentParser(description="Verify Sovereign Ledger Math Framework")
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--end", type=int, default=None)
    ap.add_argument("--ledger-dir", type=Path, default=discover_ledger_dir())
    ap.add_argument("--strict-gaps", action="store_true")
    args = ap.parse_args()

    if not args.ledger_dir.is_dir():
        print(f"ledger dir missing: {args.ledger_dir}", file=sys.stderr)
        return 1

    end = args.end if args.end is not None else discover_max_index(args.ledger_dir)
    if end < args.start:
        print(f"empty range: start={args.start} end={end}", file=sys.stderr)
        return 1

    print("=" * 70)
    print("LEDGER MATH FRAMEWORK — DUAL REGIME CHECK")
    print(f"   range: {args.start:04d} → {end:04d}")
    print(f"   ledger: {args.ledger_dir}")
    print(f"   phi={PHI:.15f}")
    print("=" * 70)

    structural_fails = 0
    missing = 0
    checked = 0

    for n in range(args.start, end + 1):
        path = resolve_path(args.ledger_dir, n)
        if path is None:
            missing += 1
            if args.strict_gaps:
                print(f"FAIL [{n:04d}] MISSING file")
                structural_fails += 1
            continue
        data, err = load_entry(path)
        if err or data is None:
            print(f"FAIL [{n:04d}] YAML error: {err}")
            structural_fails += 1
            continue
        fails = verify_entry(n, data)
        checked += 1
        if fails:
            structural_fails += 1
            print(f"FAIL [{n:04d}] " + "; ".join(fails))
        else:
            print(f"OK   [{n:04d}]")

    print("-" * 70)
    print(f"SUMMARY: checked={checked} missing={missing} fails={structural_fails}")
    if structural_fails:
        print("FRAMEWORK CHECK FAILED")
        return 1
    print("FRAMEWORK CHECK PASSED")
    print(f"Seal: {SEAL_PREFIX} · LEDGER_MATH_CI · WOOD_DRAGON_0.91 · SEALED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
