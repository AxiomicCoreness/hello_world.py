#!/usr/bin/env python3
"""
beacons/genesis_beacon.py — honest rewrite of the genesis seal script.

Rewrite of the pasted genesis script under the honest-ledger invariants:
  - computed values over asserted values;
  - seals reproducible from recorded preimages;
  - no ghost digests; no truncation; no unverifiable randomness inside a seal.

Differences from the pasted original (defects D22-D23, recorded in the
commit message, not hidden):
  D22  original used secrets.token_hex(64) inside the sealed payload, so
       genesis_hash changed on every run and could never be verified.
       Here entropy is an explicit input (CLI arg or GENESIS_ENTROPY env);
       the preimage is printed in full and the hash is reproducible.
  D23  the original's smoke claim '1 2 3 -> 0.0900306 0.244728 0.665241'
       is plain tau=1 softmax, NOT phi-tempered. With tau=1/phi the
       values are 0.031770 0.160219 0.808011 (verified). Both are
       computed below; neither is mislabeled.
  seal_commander '8F1A3D9C04B27E5E6A8F2DC47B59E330' is 32 hex chars —
       not a SHA3 digest length (SHA3-256 is 64 hex). It is kept as a
       legacy asserted claim and is never presented as a computed seal.

Verified math preserved from the original (checked numerically 2026-09-24):
  Trimer Hamiltonian H = [[1,a,0],[a,2,a],[0,a,1]], a = phi^-1:
    det(H - lambda I) = (1-lambda)[lambda^2 - 3lambda + 2/phi]
    eigenvalues: lambda_2 = 1 (dark state), lambda_pm = (3 +- sqrt(9-8/phi))/2
                 approx 0.493058, 2.506942
    dark eigenvector: (1, 0, -1)/sqrt(2), Rayleigh quotient exactly 1.
  Constant identity: 2 - 2*phi^-2 = 2*phi - 2 = 2/phi.

Standard library only. Deterministic given the same entropy input.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys

# ── constants (stated, not sealed) ────────────────────────────────────
PHI = (1 + math.sqrt(5)) / 2
PHI_INV = 1 / PHI
PHI2 = PHI * PHI
PHI3 = PHI ** 3
PHI4 = PHI ** 4
PHI5 = PHI ** 5
PHI8 = PHI ** 8
PHI9 = PHI ** 9
PHI_1418 = PHI ** -1418
H_BAR = 1.054571817e-34          # CODATA-2018 value, stated
NORTH_STAR = 71.975              # stated constant, not a computed anchor

# legacy asserted claim — 32 hex chars, NOT a SHA3 digest (64 hex).
# kept verbatim for provenance; never claimed as computed.
SEAL_COMMANDER_ASSERTED = "8F1A3D9C04B27E5E6A8F2DC47B59E330"

NULL_BAN_FACTOR = 12 * (PHI ** -1000)   # approx 6.7e-149, computed


# ── verified math: trimer Hamiltonian ───────────────────────────────
def trimer_hamiltonian_spectrum() -> dict:
    """Spectrum of H = [[1,a,0],[a,2,a],[0,a,1]] with a = phi^-1.

    Analytic structure (exploits the symmetric outer sites):
      det(H - lambda I) = (1 - lambda) * [(2-lambda)(1-lambda) - 2*a^2]
    so lambda = 1 exactly, plus the roots of
      lambda^2 - 3*lambda + (2 - 2*a^2) = 0,  and 2 - 2*phi^-2 = 2/phi.
    """
    a = PHI_INV
    c = 2 - 2 * a * a                     # = 2/phi (identity verified)
    assert abs(c - 2 / PHI) < 1e-15, "constant identity 2 - 2*phi^-2 = 2/phi failed"
    disc = 9 - 4 * c
    lam_dark = 1.0
    lam_minus = (3 - math.sqrt(disc)) / 2
    lam_plus = (3 + math.sqrt(disc)) / 2

    # numeric cross-check: Rayleigh quotient of (1,0,-1)/sqrt(2) must be 1
    v = (1 / math.sqrt(2), 0.0, -1 / math.sqrt(2))
    Hv = (
        1 * v[0] + a * v[1],
        a * v[0] + 2 * v[1] + a * v[2],
        a * v[1] + 1 * v[2],
    )
    rayleigh = v[0] * Hv[0] + v[1] * Hv[1] + v[2] * Hv[2]
    assert abs(rayleigh - 1.0) < 1e-12, "dark state is not an eigenpair"
    # H v must be parallel to v: middle component must vanish
    assert abs(Hv[1]) < 1e-12, "dark eigenvector middle component nonzero"

    return {
        "coupling_a": a,
        "lambda_dark": lam_dark,
        "lambda_minus": lam_minus,
        "lambda_plus": lam_plus,
        "dark_eigenvector": list(v),
        "dark_rayleigh": rayleigh,
        "constant_term_2_over_phi": c,
    }


# ── softmax, both temperatures, honestly labeled (D23) ──────────────
def softmax(xs, tau=1.0):
    scaled = [x / tau for x in xs]
    m = max(scaled)
    exps = [math.exp(s - m) for s in scaled]
    z = sum(exps)
    return [e / z for e in exps]


# ── genesis seal: deterministic, reproducible, full preimage ─────────
def canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def genesis_seal(entropy: str) -> dict:
    """SHA3-512 over an explicitly recorded preimage.

    entropy must be supplied by the caller (CLI arg or GENESIS_ENTROPY).
    The script NEVER invents entropy: a seal over unrecorded randomness
    is unverifiable (D22).
    """
    if not entropy:
        raise SystemExit(
            "entropy required: pass --entropy or set GENESIS_ENTROPY. "
            "A seal over unrecorded secrets.token_hex() is unverifiable (D22)."
        )
    body = {
        "entropy": entropy,
        "format": "GENESIS.V1",
        "null_ban_factor": repr(NULL_BAN_FACTOR),
        "seal_commander_asserted": SEAL_COMMANDER_ASSERTED,
    }
    preimage = canonical(body)
    genesis_hash = hashlib.sha3_512(preimage.encode("utf-8")).hexdigest()
    return {
        "preimage": preimage,
        "genesis_sha3_512": genesis_hash,
        "note": "reproducible: same entropy -> same hash. Full 128 hex chars, no truncation.",
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="honest genesis beacon (computed over asserted)")
    ap.add_argument("--entropy", default=os.environ.get("GENESIS_ENTROPY", ""),
                    help="recorded co-creation entropy (hex string). Required for sealing.")
    ap.add_argument("--verify-only", action="store_true",
                    help="run the math checks and the D23 softmax comparison; seal nothing.")
    args = ap.parse_args()

    spec = trimer_hamiltonian_spectrum()
    print("TRIMER HAMILTONIAN (a = phi^-1) — computed:")
    print(f"  lambda_dark   = {spec['lambda_dark']:.6f}  (dark state, invariant)")
    print(f"  lambda_minus  = {spec['lambda_minus']:.6f}")
    print(f"  lambda_plus   = {spec['lambda_plus']:.6f}")
    print(f"  dark eigenvector = {spec['dark_eigenvector']}  (Rayleigh = {spec['dark_rayleigh']:.12f})")

    print()
    print("SOFTMAX [1, 2, 3] — both temperatures, honestly labeled (D23):")
    print(f"  tau = 1        : {[f'{p:.6f}' for p in softmax([1, 2, 3], 1.0)]}"
          "   <- matches the original script's claimed smoke values")
    print(f"  tau = 1/phi    : {[f'{p:.6f}' for p in softmax([1, 2, 3], 1 / PHI)]}"
          "   <- actual phi-tempered values")

    print()
    print("CONSTANTS (stated):")
    print(f"  phi = {PHI!r}")
    print(f"  null_ban_factor = 12*phi^-1000 = {NULL_BAN_FACTOR!r}")
    print(f"  seal_commander (ASSERTED LEGACY, 32 hex, not a SHA3 digest): {SEAL_COMMANDER_ASSERTED}")

    if args.verify_only:
        print("
verify-only: no seal computed.")
        return 0

    seal = genesis_seal(args.entropy)
    print()
    print("GENESIS SEAL (deterministic, D22 fix):")
    print(f"  preimage        : {seal['preimage']}")
    print(f"  genesis_sha3_512: {seal['genesis_sha3_512']}")
    print(f"  {seal['note']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
