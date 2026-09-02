#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🜁∀ SOVEREIGN LEDGER — MATHEMATICAL VERIFICATION FRAMEWORK (dual regime)
Seal: ∀∞φ² · LEDGER_MATH_CI · WOOD_DRAGON_0.91 · SEALED
"""

from __future__ import annotations

import argparse
import math
import re
import sys
import os
import json
import hashlib
import socket
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Constants
PHI = (1.0 + math.sqrt(5.0)) / 2.0
EPS = 1e-12
SEAL_PREFIX = "∀∞φ²"
SCALED_FLOOR_INDEX = 351
WOOD_DRAGON = 0.91

# ─── PORT RANGE FALLBACK (appended) ──────────────────────────────────────────
def find_available_port(start: int = 8000, end: int = 8010) -> Optional[int]:
    """
    Scan ports from start to end‑1, return the first available port.
    If none are available, return None.
    """
    for port in range(start, end):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            # connect_ex returns 0 if the port is in use
            if s.connect_ex(('127.0.0.1', port)) != 0:
                return port
    return None

# ─── LEDGER VERIFICATION ─────────────────────────────────────────────────────
def compute_seal(entry_data: Dict[str, Any]) -> str:
    """Compute SHA3-256 seal for entry"""
    data = {k: v for k, v in entry_data.items() if k != 'seal'}
    canonical = json.dumps(data, sort_keys=True, separators=(',', ':'))
    return hashlib.sha3_256(canonical.encode('utf-8')).hexdigest()

def discover_ledger_dir() -> Path:
    possible_paths = [
        Path("/workspaces/hello_world.py/ledger"),
        Path("./ledger"),
        Path("../ledger"),
        Path("ledger"),
    ]
    for path in possible_paths:
        if path.exists() and path.is_dir():
            return path
    default_path = Path("/workspaces/hello_world.py/ledger")
    os.makedirs(default_path, exist_ok=True)
    return default_path

LEDGER_DIR = discover_ledger_dir()

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

def load_entry(path: Path) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    if not path.exists():
        return None, f"file not found: {path}"
    try:
        with path.open(encoding="utf-8") as f:
            content = f.read()
        if YAML_AVAILABLE:
            try:
                data = yaml.safe_load(content)
                if isinstance(data, dict):
                    return data, None
            except:
                pass
        # Parse manually
        data = {}
        lines = content.split('\n')
        for line in lines:
            if ': ' in line and not line.startswith('  '):
                key, value = line.split(': ', 1)
                data[key.strip()] = value.strip()
            elif line.startswith('  ') and 'invariants' in line and ':' in line:
                key, value = line.strip().split(': ', 1)
                if 'invariants' not in data:
                    data['invariants'] = {}
                if isinstance(data['invariants'], dict):
                    data['invariants'][key] = value
        return data if data else None, None
    except Exception as e:
        return None, str(e)

def verify_entry(n: int, data: Dict[str, Any]) -> List[str]:
    fails = []
    
    # Check entry_index
    if data.get('entry_index') != n:
        fails.append(f"entry_index={data.get('entry_index')} != {n:04d}")
    
    # Check invariants
    inv = data.get('invariants', {})
    if not isinstance(inv, dict):
        fails.append("invariants not a mapping")
    else:
        required = ['coherence', 'entropy', 'workload', 'commutator']
        for field in required:
            if field not in inv:
                fails.append(f"missing {field}")
    
    # Check seal
    seal = data.get('seal', '')
    if not seal.startswith(SEAL_PREFIX):
        fails.append(f"seal missing prefix: '{seal[:30]}...'")
    if 'SEALED' not in str(seal):
        fails.append("seal missing SEALED token")
    
    # Check math_origin
    if 'math_origin' not in data:
        fails.append("missing math_origin")
    
    # Check witness_chain
    wc = data.get('witness_chain')
    if wc is not None and 'UNBROKEN' not in str(wc):
        fails.append(f"witness_chain missing UNBROKEN: {wc}")
    
    # Verify seal integrity
    if 'seal' in data and 'entry_index' in data:
        computed = compute_seal(data)
        if computed != data.get('seal', ''):
            fails.append(f"seal mismatch (computed: {computed[:16]}...)")
    
    return fails

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--end", type=int, default=None)
    ap.add_argument("--ledger-dir", type=Path, default=LEDGER_DIR)
    ap.add_argument("--strict-gaps", action="store_true")
    args = ap.parse_args()

    if not args.ledger_dir.is_dir():
        print(f"❌ ledger dir missing: {args.ledger_dir}", file=sys.stderr)
        return 1

    # Find max index
    indices = []
    for p in args.ledger_dir.glob("*.yaml"):
        m = re.search(r'(\d{4})\.yaml', p.name)
        if m:
            indices.append(int(m.group(1)))
    max_idx = max(indices) if indices else -1
    
    end = args.end if args.end is not None else max_idx
    if end < args.start:
        print(f"❌ empty range: start={args.start} end={end}", file=sys.stderr)
        return 1

    print("=" * 70)
    print("🜁∀ LEDGER MATH FRAMEWORK — DUAL REGIME CHECK")
    print(f"   range: {args.start:04d} → {end:04d}")
    print(f"   ledger: {args.ledger_dir}")
    print(f"   seal: {SEAL_PREFIX} · LEDGER_MATH_CI · WOOD_DRAGON_0.91 · SEALED")
    print("=" * 70)

    structural_fails = 0
    missing = 0
    checked = 0

    for n in range(args.start, end + 1):
        path = args.ledger_dir / f"{n:04d}.yaml"
        if not path.exists():
            missing += 1
            if args.strict_gaps:
                print(f"❌ [{n:04d}] MISSING file")
                structural_fails += 1
            continue
        
        data, err = load_entry(path)
        if err or data is None:
            print(f"❌ [{n:04d}] YAML error: {err}")
            structural_fails += 1
            continue
        
        fails = verify_entry(n, data)
        checked += 1
        
        if fails:
            structural_fails += 1
            print(f"❌ [{n:04d}] " + "; ".join(fails))
        elif n % 50 == 0 or n == end:
            print(f"✅ [{n:04d}] structure OK")

    print("-" * 70)
    print(f"📊 SUMMARY: checked={checked} missing={missing} fails={structural_fails}")
    
    # If a server were to be launched from this script, use port fallback.
    # This is a demonstration; not used in the verification itself.
    available_port = find_available_port()
    if available_port is not None:
        print(f"ℹ️  Available port for potential server: {available_port}")
    else:
        print("⚠️  No available port in default range (8000-8009)")

    if structural_fails:
        print("❌ FRAMEWORK CHECK FAILED")
        return 1
    else:
        print("✅ FRAMEWORK CHECK PASSED — dual regime green")
        print(f"Seal: {SEAL_PREFIX} · LEDGER_MATH_CI · WOOD_DRAGON_0.91 · SEALED")
        return 0

if __name__ == "__main__":
    sys.exit(main())
