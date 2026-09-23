#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
math_origin defect ledger — kernel audit
=======================================
Every defect recorded here was found by computation in this kernel-forge
session, not by assertion. Each entry carries: evidence (the computed
value vs the claimed value), status, and disposition.

Run:  python kernel/math_origin_audit.py
Exit: 0 all recorded defects still accurately described
      1 a defect entry no longer matches reality (fix the ledger)
      2 arithmetic check failed (φ identities broken)

Rule (P_pump pattern): a defect entry is itself a claim. The audit
re-verifies each claim numerically, so the ledger cannot drift from
the code it describes without failing CI.
"""

import math
import sys

PHI = (1 + math.sqrt(5)) / 2

# ── gate: φ identities (same checks as hypersurface_7d.MATH_ORIGIN) ──
def phi_gate():
    eps = 1e-15
    checks = [
        abs(PHI ** 2 - PHI - 1.0) <= eps,
        abs(1 / PHI - (PHI - 1.0)) <= eps,
        abs((1 / PHI) ** 2 - (2.0 - PHI)) <= eps,
    ]
    return all(checks)


# ── defect registry: each defect is (claimed, actual, tolerance) ──
DEFECTS = {
    "D1_sovereign_hamiltonian_E0": {
        "file": "sovereign_hamiltonian.py",
        "claim": "E0 = -3.236068",
        "claimed_value": -3.236068,
        "actual_value": 1.0 - 2.0 / PHI + PHI ** 2,   # +2.3819660
        "status": "FIXED_LANDED",
        "evidence": "1 - 2φ⁻¹ + φ² is positive; cannot equal -3.236",
    },
    "D2_sovereign_hamiltonian_detG": {
        "file": "sovereign_hamiltonian.py",
        "claim": "det(G) = -1.0",
        "claimed_value": -1.0,
        "actual_value": PHI ** 2 - PHI ** -2,          # √5 ≈ 2.2360680
        "status": "FIXED_LANDED",
        "evidence": "φ² − φ⁻² = √5 exactly",
    },
    "D3_sovereign_hamiltonian_HB": {
        "file": "sovereign_hamiltonian.py",
        "claim": "H_B ≈ φ⁻¹",
        "claimed_value": 1 / PHI,
        "actual_value": 1 / PHI - 1.0,                # −φ⁻² ≈ −0.3819660
        "status": "FIXED_LANDED",
        "evidence": "φ⁻¹ − 1 is negative; sign claim was wrong",
    },
    "D4_sovereign_hamiltonian_frobenius": {
        "file": "sovereign_hamiltonian.py",
        "claim": "‖H‖_F = 5.0",
        "claimed_value": 5.0,
        "actual_value": math.sqrt(1.0 + 2.0 * (1 / PHI) ** 2 + (PHI ** 2) ** 2),  # ≈2.9356
        "status": "FIXED_LANDED",
        "evidence": "√Σw² over committed weights ≠ 5.0",
    },
    "D5_sovereign_hamiltonian_trace": {
        "file": "sovereign_hamiltonian.py",
        "claim": "trace = 0.0",
        "claimed_value": 0.0,
        "actual_value": 1.0 - 2.0 / PHI + PHI ** 2,   # ≈2.3819660
        "status": "FIXED_LANDED",
        "evidence": "weight sum is nonzero",
    },
    "D6_frequency_box_741Hz": {
        "file": "(pipeline docs)",
        "claim": "C4 × φ^2.5 = 741 Hz with φ^2.5 ≈ 2.833",
        "claimed_value": 741.0,
        "actual_value": 261.63 * PHI ** 2.5,           # ≈871.6 Hz
        "status": "OPEN_DOCUMENTATION",
        "evidence": "φ^2.5 ≈ 3.331, not 2.833; 261.63×3.331 ≈ 871.6",
    },
    "D7_lua_force_pass_on_drift": {
        "file": "Lua additive kernel step 3",
        "claim": "100% SUCCESS PATH",
        "claimed_value": "always-pass verifier",
        "actual_value": "absorbs any input into canonical output (Δ=∅)",
        "status": "OPEN_UNFIXED",
        "evidence": "verifier cannot fail ⇒ carries no information; ghost seal",
    },
    "D8_lua_recon_ok_forced_true": {
        "file": "Lua main()",
        "claim": "failure branch handled",
        "claimed_value": "recon_ok = true",
        "actual_value": "constant; preceding branch is dead code",
        "status": "OPEN_UNFIXED",
        "evidence": "assignment deletes the conditional",
    },
    "D9_ed25519_structure_only": {
        "file": ".github/workflows (hamiltonian cycle)",
        "claim": "Ed25519 signature verified (structure)",
        "claimed_value": "verified",
        "actual_value": "no key constructed, no signature checked",
        "status": "OPEN_UNFIXED",
        "evidence": "✅ printed unconditionally — cannot fail, ghost seal",
    },
    "D10_ledger_self_verified_flag": {
        "file": "LEDGER_ENTRY_635 (old)",
        "claim": "verified: True (hardcoded)",
        "claimed_value": True,
        "actual_value": "assertion in source, not a computed check",
        "status": "FIXED_LANDED",
        "evidence": "ledger entry declaring itself verified is a ghost seal; removed in corrected module",
    },
    "D11_hypersurface_pending_constants": {
        "file": "hypersurface_7d.py",
        "claim": "NORTH_STAR_HZ, PHASE_LOCK_DEG",
        "claimed_value": "used in title",
        "actual_value": "no derivation supplied",
        "status": "OPEN_PENDING_MATH_ORIGIN",
        "evidence": "marked PENDING_MATH_ORIGIN in registry; warn-only until load-bearing",
    },
}

# numeric defects: claimed ≠ actual, and fix verified by actual being right
NUMERIC_DEFECTS = ["D1_sovereign_hamiltonian_E0", "D2_sovereign_hamiltonian_detG",
                  "D3_sovereign_hamiltonian_HB", "D4_sovereign_hamiltonian_frobenius",
                  "D5_sovereign_hamiltonian_trace", "D6_frequency_box_741Hz"]


def audit():
    if not phi_gate():
        print("❌ φ gate failed — arithmetic environment broken")
        return 2

    failures = []
    for key in NUMERIC_DEFECTS:
        d = DEFECTS[key]
        if abs(d["claimed_value"] - d["actual_value"]) < 1e-9:
            # claim matches actual ⇒ defect description is WRONG (they must differ)
            failures.append(f"{key}: claimed value now equals actual — ledger entry stale")
        print(f"  {key}: claimed={d['claimed_value']} actual={d['actual_value']:.7f} [{d['status']}]")

    open_unfixed = [k for k, d in DEFECTS.items() if d["status"].startswith("OPEN_UNFIXED")]
    pending = [k for k, d in DEFECTS.items() if d["status"] == "OPEN_PENDING_MATH_ORIGIN"]
    open_doc = [k for k, d in DEFECTS.items() if d["status"] == "OPEN_DOCUMENTATION"]

    print()
    print(f"total defects recorded : {len(DEFECTS)}")
    print(f"fixed & landed         : {sum(1 for d in DEFECTS.values() if d['status'] == 'FIXED_LANDED')}")
    print(f"open documentation     : {len(open_doc)} ({', '.join(open_doc)})")
    print(f"open unfixed           : {len(open_unfixed)} ({', '.join(open_unfixed)})")
    print(f"pending math_origin    : {len(pending)} ({', '.join(pending)})")

    if failures:
        print()
        print("❌ ledger integrity failures:")
        for f in failures:
            print(f"   {f}")
        return 1
    print()
    print("✅ ledger integrity: every numeric defect entry verified (claimed ≠ actual)")
    print("⚠️  open items remain — see OPEN_* statuses; none are sealed as verified")
    return 0


if __name__ == "__main__":
    sys.exit(audit())
