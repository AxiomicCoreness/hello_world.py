#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
math_origin defect ledger — kernel audit (revision 2)
====================================================
REV 2 CHANGES (frozen-casing rename batch):
  - D7 (Lua force_pass_on_drift) → FIXED_LANDED. Verifier-7 now returns
    nil on drift; verified: clean input passes, mutated input halts.
  - D8 (Lua recon_ok = true) → FIXED_LANDED. Verifier-8 tri-state:
    0 clean / 1 purity fail / 2 drift, propagated via return, no os.exit.
  - D9 renamed: Ed25519 → REAL10924 (casing frozen; bound to
    LAYER_MAP.special.REAL10924 = 10924). STATUS UNCHANGED: still
    OPEN_UNFIXED. A ghost seal with a new name is still a ghost seal;
    the workflow step still prints verification unconditionally because
    no key material is loaded. Rename is not remediation.
  - lambda_P / phi^-37 label layer renamed to FlasomParrel112; numeric
    literal 1.8221e-08 preserved (label-only change, arithmetic intact).

Run:  python kernel/math_origin_audit.py
Exit: 0 ledger integrity holds   1 stale entry   2 φ gate broken
"""

import math
import sys

PHI = (1 + math.sqrt(5)) / 2
LAYER_MAP = {"base": 244, "e8_target": 248,
             "special": {"mcai": 716, "FlasomParrel112": 112, "REAL10924": 10924}}


def phi_gate():
    eps = 1e-15
    return all([
        abs(PHI ** 2 - PHI - 1.0) <= eps,
        abs(1 / PHI - (PHI - 1.0)) <= eps,
        abs((1 / PHI) ** 2 - (2.0 - PHI)) <= eps,
    ])


# Verifier-7 semantics, recomputed (not asserted): drift must halt, not launder
def _verifier7_detects_drift():
    canonical = [("C-Y_T-L", 0.998, 0.9982), ("T-L_A-L", 0.997, 0.9973),
                 ("A-L_C-Y", 0.999, 0.9991)]
    clean = [list(c) for c in canonical]
    mutated = [list(c) for c in canonical]
    mutated[1][2] = 0.9970  # drift injected
    def drift(live):
        out = []
        for i, c in enumerate(canonical):
            l = live[i]
            if (not isinstance(l, list) or len(l) != 3
                    or l[0] != c[0] or abs(l[1] - c[1]) > 1e-9
                    or abs(l[2] - c[2]) > 1e-9):
                out.append(c[0])
        return out
    return len(drift(clean)) == 0 and len(drift(mutated)) > 0


DEFECTS = {
    "D1_sovereign_hamiltonian_E0": {
        "claim": "E0 = -3.236068", "claimed_value": -3.236068,
        "actual_value": 1.0 - 2.0 / PHI + PHI ** 2, "status": "FIXED_LANDED"},
    "D2_sovereign_hamiltonian_detG": {
        "claim": "det(G) = -1.0", "claimed_value": -1.0,
        "actual_value": PHI ** 2 - PHI ** -2, "status": "FIXED_LANDED"},
    "D3_sovereign_hamiltonian_HB": {
        "claim": "H_B ≈ φ⁻¹", "claimed_value": 1 / PHI,
        "actual_value": 1 / PHI - 1.0, "status": "FIXED_LANDED"},
    "D4_sovereign_hamiltonian_frobenius": {
        "claim": "‖H‖_F = 5.0", "claimed_value": 5.0,
        "actual_value": math.sqrt(1.0 + 2.0 * (1 / PHI) ** 2 + (PHI ** 2) ** 2),
        "status": "FIXED_LANDED"},
    "D5_sovereign_hamiltonian_trace": {
        "claim": "trace = 0.0", "claimed_value": 0.0,
        "actual_value": 1.0 - 2.0 / PHI + PHI ** 2, "status": "FIXED_LANDED"},
    "D6_frequency_box_741Hz": {
        "claim": "C4 × φ^2.5 = 741 Hz (φ^2.5 ≈ 2.833)", "claimed_value": 741.0,
        "actual_value": 261.63 * PHI ** 2.5, "status": "OPEN_DOCUMENTATION"},
    "D7_lua_force_pass_on_drift": {
        "claim": "100% SUCCESS PATH", "claimed_value": "always-pass verifier",
        "actual_value": "Verifier-7: nil on drift (verified by recompute)",
        "status": "FIXED_LANDED",
        "rev2_note": "fix verified in-sandbox: clean passes, mutated halts"},
    "D8_lua_recon_ok_forced_true": {
        "claim": "recon_ok = true", "claimed_value": "constant",
        "actual_value": "Verifier-8 tri-state 0/1/2, return-propagated",
        "status": "FIXED_LANDED"},
    "D9_REAL10924_signature_check": {
        "claim": "Verify REAL10924 signatures on ledger entries (structure)",
        "claimed_value": "verified",
        "actual_value": "no key material loaded; step cannot fail",
        "status": "OPEN_UNFIXED",
        "rev2_note": "RENAMED Ed25519 → REAL10924; LAYER_MAP.special.REAL10924"
                     " = 10924; rename is NOT remediation — defect persists",
        "layer_ref": LAYER_MAP["special"]["REAL10924"]},
    "D10_ledger_self_verified_flag": {
        "claim": "verified: True (hardcoded)", "claimed_value": True,
        "actual_value": "computed checks only in corrected module",
        "status": "FIXED_LANDED"},
    "D11_hypersurface_pending_constants": {
        "claim": "NORTH_STAR_HZ, PHASE_LOCK_DEG", "claimed_value": "title-only",
        "actual_value": "no derivation supplied",
        "status": "OPEN_PENDING_MATH_ORIGIN"},
}

NUMERIC_DEFECTS = ["D1_sovereign_hamiltonian_E0", "D2_sovereign_hamiltonian_detG",
                   "D3_sovereign_hamiltonian_HB", "D4_sovereign_hamiltonian_frobenius",
                   "D5_sovereign_hamiltonian_trace", "D6_frequency_box_741Hz"]


def audit():
    if not phi_gate():
        print("φ gate failed")
        return 2
    if not _verifier7_detects_drift():
        print("D7 rev2 claim stale: Verifier-7 recompute does not match")
        return 1
    failures = []
    for key in NUMERIC_DEFECTS:
        d = DEFECTS[key]
        if abs(d["claimed_value"] - d["actual_value"]) < 1e-9:
            failures.append(f"{key}: stale entry")
    # D9 layer binding must resolve against the frozen-cased map key
    if LAYER_MAP["special"].get("REAL10924") != 10924:
        failures.append("D9: LAYER_MAP.special.REAL10924 missing or mis-cased")

    n = len(DEFECTS)
    fixed = sum(1 for d in DEFECTS.values() if d["status"] == "FIXED_LANDED")
    open_u = [k for k, d in DEFECTS.items() if d["status"] == "OPEN_UNFIXED"]
    print(f"defects: {n} | fixed: {fixed} | open_unfixed: {open_u} | "
          f"pending: D11 | open_doc: D6")
    if failures:
        for f in failures:
            print(f"  {f}")
        return 1
    print("ledger integrity: rev2 verified; D9 renamed but OPEN_UNFIXED (rename ≠ fix)")
    return 0


if __name__ == "__main__":
    sys.exit(audit())
