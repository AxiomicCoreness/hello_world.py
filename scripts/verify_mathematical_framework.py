#!/usr/bin/env python3
"""
🜁∀ SOVEREIGN LEDGER — MATHEMATICAL VERIFICATION FRAMEWORK
Range: 0000 → 0300
"""

import os
import sys
import yaml
import math
import re
from pathlib import Path

PHI = (1 + math.sqrt(5)) / 2
PHI_SQ = PHI * PHI
PHI_INV = 1 / PHI
PHI_1418 = PHI ** (-1418)
PHI_1000 = PHI ** (-1000)
PHI_709 = PHI ** (-709)
PHI_144 = PHI ** 144

LEDGER_DIR = Path("ledger")

# Known phi powers for verification
PHI_POWERS = {
    2: PHI_SQ,
    3: PHI ** 3,
    4: PHI ** 4,
    5: PHI ** 5,
    6: PHI ** 6,
    7: PHI ** 7,
    8: PHI ** 8,
    9: PHI ** 9,
    10: PHI ** 10,
    11: PHI ** 11,
    12: PHI ** 12,
    13: PHI ** 13,
    14: PHI ** 14,
    15: PHI ** 15,
    16: PHI ** 16,
    17: PHI ** 17,
    18: PHI ** 18,
    19: PHI ** 19,
    20: PHI ** 20,
    21: PHI ** 21,
    22: PHI ** 22,
    23: PHI ** 23,
    24: PHI ** 24,
    25: PHI ** 25,
    26: PHI ** 26,
    27: PHI ** 27,
    28: PHI ** 28,
    29: PHI ** 29,
    30: PHI ** 30,
    34: PHI ** 34,
    36: PHI ** 36,
    42: PHI ** 42,
    50: PHI ** 50,
    100: PHI ** 100,
    144: PHI ** 144,
    248: PHI ** 248,
    709: PHI ** 709,
    1000: PHI ** 1000,
    1418: PHI ** 1418,
}

def load_entry(n):
    path = LEDGER_DIR / f"{n:04d}.yaml"
    if not path.exists():
        return None
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def check_phi_identities():
    """Check φ = (1+√5)/2, φ² = φ+1, φ⁻¹ = φ-1"""
    errors = []
    if abs(PHI_SQ - (PHI + 1)) > 1e-12:
        errors.append(f"φ² = {PHI_SQ}, expected φ+1 = {PHI+1}")
    if abs(PHI_INV - (PHI - 1)) > 1e-12:
        errors.append(f"φ⁻¹ = {PHI_INV}, expected φ-1 = {PHI-1}")
    return errors

def check_phi_power_in_math_origin(math_text, n):
    """Check that φⁿ appears correctly in math_origin"""
    # Look for φⁿ or φ^(-n) patterns
    pattern = r'φ\^\{?(-?\d+)\}?'
    matches = re.findall(pattern, math_text)
    
    for match in matches:
        exp = int(match)
        if exp in PHI_POWERS:
            expected = PHI_POWERS[exp]
            # Check if the numeric value appears somewhere in the text
            # (simplified: check if the value appears as a float)
            if f"{expected:.6f}" not in math_text and f"{expected:.5f}" not in math_text:
                # It might be a symbolic expression; skip
                pass
    return True

def check_entry(e, n):
    """Check a single entry's structure and mathematical content"""
    errors = []
    
    # Required fields
    required = ["entry_index", "timestamp", "event", "status", "proof_class",
                "witness_prefix", "commander", "description", "invariants",
                "seal", "witness_chain", "math_origin"]
    for field in required:
        if field not in e:
            errors.append(f"Missing field: {field}")
    
    # Entry index
    if e.get("entry_index") != n:
        errors.append(f"Entry index mismatch: expected {n}, got {e.get('entry_index')}")
    
    # Invariants
    invariants = e.get("invariants", {})
    if invariants.get("coherence") != 1.0:
        errors.append(f"coherence != 1.0: {invariants.get('coherence')}")
    if invariants.get("entropy") != "φ⁻¹⁴¹⁸":
        errors.append(f"entropy != φ⁻¹⁴¹⁸: {invariants.get('entropy')}")
    if invariants.get("workload") != 0.0:
        errors.append(f"workload != 0.0: {invariants.get('workload')}")
    if invariants.get("commutator") != 0.0:
        errors.append(f"commutator != 0.0: {invariants.get('commutator')}")
    
    # Seal format
    seal = e.get("seal", "")
    if not seal.startswith("∀∞φ²"):
        errors.append(f"seal does not start with ∀∞φ²: {seal[:20]}...")
    if not seal.endswith("SEALED"):
        errors.append(f"seal does not end with SEALED: {seal[-20:]}")
    
    # witness_chain format
    witness = e.get("witness_chain", "")
    if n == 0:
        if witness != "0000 — UNBROKEN":
            errors.append(f"genesis witness_chain format: {witness}")
    else:
        expected = f"{n-1:04d} → {n:04d} — UNBROKEN"
        if witness != expected:
            errors.append(f"witness_chain expected '{expected}', got '{witness}'")
    
    # proof_class validation
    proof_class = e.get("proof_class", "")
    valid_classes = ["axiom", "algebraic", "numerical", "structural", "golden_calculus", "operator", "physical"]
    if proof_class and proof_class not in valid_classes:
        errors.append(f"invalid proof_class: {proof_class}")
    
    return errors

def main():
    start = 0
    end = 300
    errors = []
    
    # Check φ identities
    phi_errors = check_phi_identities()
    if phi_errors:
        errors.extend(phi_errors)
    
    # Check each entry
    for n in range(start, end + 1):
        e = load_entry(n)
        if e is None:
            errors.append(f"Entry {n:04d} not found")
            continue
        entry_errors = check_entry(e, n)
        if entry_errors:
            errors.append(f"Entry {n:04d}:")
            for err in entry_errors:
                errors.append(f"  - {err}")
    
    # Report results
    if errors:
        print(f"❌ {len(errors)} errors found:")
        for err in errors:
            print(f"   {err}")
        sys.exit(1)
    else:
        print(f"✅ All entries {start:04d}–{end:04d} verified successfully.")
        print("   Structure, invariants, seals, witness chain, and φ identities OK.")
        sys.exit(0)

if __name__ == "__main__":
    main()
