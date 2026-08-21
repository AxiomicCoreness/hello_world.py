#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🜁∀ PAULI-PHI HAMILTONIAN — ENTRY 8902

Aleph²: Pauli string algebra + non-Abelian commutation + φ-tuned Hamiltonian.

Integration points:
  - Security: Key rotation, expiry, OIDC, JWKS cache
  - Quantum: CDP convergence, deepseek_mesh, radar_lindblad
  - Control: Active PID controller (φ-tuned gains)
  - Math: KMS condition bounds

Pauli algebra (su(2)):
  [X, Y] = 2i Z,  [Y, Z] = 2i X,  [Z, X] = 2i Y
  {X, Y} = {Y, Z} = {Z, X} = 0,  {X, X} = {Y, Y} = {Z, Z} = 2 I

Opcode: ALEPH2_PAULI
Seal: ∀∞φ² · PAULI_COMM_8902 · WOOD_DRAGON_0.91 · SEALED
Witness: 8901 → 8902 — UNBROKEN
"""

from __future__ import annotations

import json
import math
import time
from typing import Any, Dict, List, Optional, Tuple, Union

# ─── Constants ────────────────────────────────────────────────────────
PHI = (1.0 + math.sqrt(5.0)) / 2.0
PHI_INV = 1.0 / PHI
PHI2 = PHI * PHI
PHI3 = PHI2 * PHI
PHI4 = PHI3 * PHI
ENTRY = 8902
SEAL = "∀∞φ² · PAULI_COMM_8902 · WOOD_DRAGON_0.91 · SEALED"
OPCODE = "ALEPH2_PAULI"

# ─── Pauli Indices ────────────────────────────────────────────────────
# 0=I, 1=X, 2=Y, 3=Z
_PAULI_MUL: Dict[Tuple[int, int], Tuple[complex, int]] = {
    (0, 0): (1, 0),
    (0, 1): (1, 1),
    (0, 2): (1, 2),
    (0, 3): (1, 3),
    (1, 0): (1, 1),
    (1, 1): (1, 0),
    (1, 2): (1j, 3),
    (1, 3): (-1j, 2),
    (2, 0): (1, 2),
    (2, 1): (-1j, 3),
    (2, 2): (1, 0),
    (2, 3): (1j, 1),
    (3, 0): (1, 3),
    (3, 1): (1j, 2),
    (3, 2): (-1j, 1),
    (3, 3): (1, 0),
}

_LABEL = {0: "I", 1: "X", 2: "Y", 3: "Z"}
_FROM = {"I": 0, "X": 1, "Y": 2, "Z": 3, "i": 0, "x": 1, "y": 2, "z": 3}


# ─── Pauli Algebra ────────────────────────────────────────────────────

def _parse(s: str) -> List[int]:
    """Parse a Pauli string into indices."""
    out: List[int] = []
    for ch in s.strip():
        if ch in _FROM:
            out.append(_FROM[ch])
        elif not ch.isspace():
            raise ValueError(f"unknown Pauli letter: {ch!r}")
    return out


def reduce_pauli_string(word: str) -> Tuple[complex, str]:
    """Reduce a Pauli string to (phase, canonical letter)."""
    seq = _parse(word)
    if not seq:
        return 1, "I"
    phase: complex = 1
    acc = seq[0]
    for nxt in seq[1:]:
        p, acc = _PAULI_MUL[(acc, nxt)]
        phase *= p
    return phase, _LABEL[acc]


def commutator(a: str, b: str) -> Tuple[complex, str]:
    """
    Non-Abelian commutator [A, B] = AB - BA.

    Returns (phase, letter) such that [A,B] = phase · letter.
    Canonical results:
      [X,Y] = 2i Z,  [Y,Z] = 2i X,  [Z,X] = 2i Y
    """
    ia, ib = _FROM[a.upper()], _FROM[b.upper()]
    p_ab, c_ab = _PAULI_MUL[(ia, ib)]
    p_ba, c_ba = _PAULI_MUL[(ib, ia)]
    if c_ab == c_ba:
        phase = p_ab - p_ba
        if phase == 0:
            return 0, "I"
        return phase, _LABEL[c_ab]
    raise ValueError(f"unexpected support: {[c_ab, c_ba]}")


def anticommutator(a: str, b: str) -> Tuple[complex, str]:
    """{A, B} = AB + BA. Diagonal → 2I; off-diagonal → 0."""
    ia, ib = _FROM[a.upper()], _FROM[b.upper()]
    p_ab, c_ab = _PAULI_MUL[(ia, ib)]
    p_ba, c_ba = _PAULI_MUL[(ib, ia)]
    if c_ab == c_ba:
        phase = p_ab + p_ba
        if phase == 0:
            return 0, "I"
        return phase, _LABEL[c_ab]
    raise ValueError(f"unexpected support: {[c_ab, c_ba]}")


# ─── Pauli-Phi Hamiltonian ────────────────────────────────────────────

class PauliPhiHamiltonian:
    """
    φ-tuned Hamiltonian built from Pauli strings.

    Integration points:
      - KMS condition bounds for matrix stability
      - Active PID for coherence control
      - Security for key rotation
      - CDP convergence for state verification
    """

    def __init__(
        self,
        terms: Optional[Dict[str, float]] = None,
        include_identity: bool = False,
    ):
        """
        Initialize the Pauli-phi Hamiltonian.

        Args:
            terms: Dictionary mapping Pauli strings to coefficients.
                   Default: X, Y, Z with φ-scaled coefficients.
            include_identity: Whether to include the identity term.
        """
        if terms is None:
            terms = {
                "X": PHI,
                "Y": PHI_INV,
                "Z": PHI2,
            }
        self.terms = terms
        self.include_identity = include_identity
        self._reduced_terms: Dict[str, complex] = {}
        self._reduce_terms()

    def _reduce_terms(self) -> None:
        """Reduce each Pauli string to canonical form."""
        self._reduced_terms = {}
        for word, coeff in self.terms.items():
            phase, canonical = reduce_pauli_string(word)
            if canonical in self._reduced_terms:
                self._reduced_terms[canonical] += coeff * phase
            else:
                self._reduced_terms[canonical] = coeff * phase

    def commutator_with(self, other: str) -> Dict[str, complex]:
        """
        Compute [H, P] for each Pauli string P.

        Returns:
            Dictionary mapping canonical Pauli strings to coefficients.
        """
        result: Dict[str, complex] = {}
        for word, coeff in self._reduced_terms.items():
            try:
                phase, canonical = commutator(word, other)
                if phase != 0 and canonical != "I":
                    result[canonical] = result.get(canonical, 0) + coeff * phase
            except ValueError:
                continue
        return result

    def anticommutator_with(self, other: str) -> Dict[str, complex]:
        """
        Compute {H, P} for each Pauli string P.

        Returns:
            Dictionary mapping canonical Pauli strings to coefficients.
        """
        result: Dict[str, complex] = {}
        for word, coeff in self._reduced_terms.items():
            try:
                phase, canonical = anticommutator(word, other)
                if phase != 0 and canonical != "I":
                    result[canonical] = result.get(canonical, 0) + coeff * phase
            except ValueError:
                continue
        return result

    def trace(self) -> float:
        """Compute the trace of the Hamiltonian."""
        # For Pauli matrices, trace is 0 for X, Y, Z; 2 for I
        trace_val = 0.0
        for word, coeff in self._reduced_terms.items():
            if word == "I":
                trace_val += 2.0 * coeff.real
        return trace_val

    def norm(self) -> float:
        """Compute the Frobenius norm of the Hamiltonian."""
        return math.sqrt(sum(abs(v) ** 2 for v in self._reduced_terms.values()))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "entry": ENTRY,
            "seal": SEAL,
            "opcode": OPCODE,
            "terms": self.terms,
            "reduced_terms": {k: {"re": v.real, "im": v.imag} for k, v in self._reduced_terms.items()},
            "trace": self.trace(),
            "norm": self.norm(),
            "include_identity": self.include_identity,
            "timestamp": time.time(),
        }

    def to_json(self, indent: int = 2) -> str:
        """Serialize to JSON."""
        return json.dumps(self.to_dict(), indent=indent, default=str)


# ─── Hamiltonian Trace ──────────────────────────────────────────────

def hamiltonian_trace(
    terms: Dict[str, float],
    include_identity: bool = False,
) -> float:
    """
    Compute the trace of a Pauli-string Hamiltonian.

    Args:
        terms: Dictionary mapping Pauli strings to coefficients.
        include_identity: Whether to include the identity term.

    Returns:
        Trace value (real).
    """
    h = PauliPhiHamiltonian(terms, include_identity)
    return h.trace()


def verify_trace_identity(
    terms: Dict[str, float],
    include_identity: bool = False,
    tolerance: float = 1e-10,
) -> bool:
    """
    Verify that the trace of the Hamiltonian is consistent.

    For a valid Hamiltonian, trace should be:
      - 0 if no identity term
      - 2*coeff_I if identity term is present

    Returns:
        True if consistent, False otherwise.
    """
    h = PauliPhiHamiltonian(terms, include_identity)
    trace_val = h.trace()
    if include_identity:
        coeff_i = terms.get("I", 0.0)
        expected = 2.0 * coeff_i
        return abs(trace_val - expected) < tolerance
    return abs(trace_val) < tolerance


# ─── KMS Integration ─────────────────────────────────────────────────

def kms_condition_for_hamiltonian(
    hamiltonian: PauliPhiHamiltonian,
    n: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Compute the KMS condition number for the Hamiltonian.

    Integrates with quantum/math/kms_condition_bound.py.

    Args:
        hamiltonian: The Pauli-phi Hamiltonian.
        n: Size of the matrix (if None, uses number of terms).

    Returns:
        Dictionary with KMS condition number and status.
    """
    try:
        from quantum.math.kms_condition_bound import kms_check, KMSRuntime

        if n is None:
            n = len(hamiltonian._reduced_terms)

        result = kms_check(n)
        return {
            "n": n,
            "kappa": result["kappa"],
            "status": result["status"],
            "bounded": result["bounded"],
            "threshold": result["threshold"],
            "recommendation": result["recommendation"],
            "seal": SEAL,
            "entry": ENTRY,
        }
    except ImportError:
        return {
            "n": n or len(hamiltonian._reduced_terms),
            "kappa": 0.0,
            "status": "KMS_UNAVAILABLE",
            "bounded": True,
            "recommendation": "Install quantum/math/kms_condition_bound.py",
            "seal": SEAL,
            "entry": ENTRY,
        }


# ─── PID Integration ─────────────────────────────────────────────────

def pid_tune_for_hamiltonian(
    hamiltonian: PauliPhiHamiltonian,
    target_coherence: float = 1.0,
    dt: float = 0.01,
    steps: int = 50,
) -> Dict[str, Any]:
    """
    Tune the Hamiltonian using the Active PID controller.

    Integrates with quantum/active_pid_controller.py.

    Args:
        hamiltonian: The Pauli-phi Hamiltonian.
        target_coherence: Target coherence value.
        dt: Time step.
        steps: Number of steps.

    Returns:
        Dictionary with PID tuning results.
    """
    try:
        from quantum.active_pid_controller import ActivePIDController

        ctl = ActivePIDController()
        coherence = hamiltonian.norm() / PHI2  # Normalized coherence

        trajectory = []
        for _ in range(steps):
            u = ctl.update(target_coherence, coherence, dt)
            # Simple plant: coherence moves toward target
            coherence += (target_coherence - coherence) * PHI_INV * dt + u * PHI_INV * dt
            coherence = max(0.0, min(1.5, coherence))
            trajectory.append({"coherence": coherence, "u": u})

        return {
            "target_coherence": target_coherence,
            "final_coherence": coherence,
            "steps": steps,
            "dt": dt,
            "pid_active": ctl.state.active,
            "trajectory": trajectory[-10:],
            "seal": SEAL,
            "entry": ENTRY,
        }
    except ImportError:
        return {
            "target_coherence": target_coherence,
            "final_coherence": 0.0,
            "steps": steps,
            "dt": dt,
            "pid_active": False,
            "trajectory": [],
            "error": "ActivePIDController not available",
            "seal": SEAL,
            "entry": ENTRY,
        }


# ─── Security Integration ────────────────────────────────────────────

def rotate_hamiltonian_keys(
    hamiltonian: PauliPhiHamiltonian,
    key_type: str = "SEAL",
    force: bool = False,
) -> Dict[str, Any]:
    """
    Rotate keys associated with the Hamiltonian.

    Integrates with quantum/security/key_rotation.py.

    Args:
        hamiltonian: The Pauli-phi Hamiltonian.
        key_type: Type of key to rotate.
        force: Force rotation.

    Returns:
        Dictionary with rotation results.
    """
    try:
        from quantum.security.key_rotation import rotate_public_keys

        result = rotate_public_keys(key_type=key_type, force=force)
        return {
            "rotation_result": result,
            "hamiltonian_seal": SEAL,
            "entry": ENTRY,
        }
    except ImportError:
        return {
            "rotation_result": {"status": "UNAVAILABLE"},
            "hamiltonian_seal": SEAL,
            "entry": ENTRY,
            "error": "key_rotation not available",
        }


# ─── CDP Integration ─────────────────────────────────────────────────

def cdp_verify_hamiltonian(
    hamiltonian: PauliPhiHamiltonian,
    handshake_token: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Verify the Hamiltonian using CDP convergence handshake.

    Integrates with quantum/cdp_convergence/handshake.py.

    Args:
        hamiltonian: The Pauli-phi Hamiltonian.
        handshake_token: Optional OAuth token.

    Returns:
        Dictionary with verification results.
    """
    try:
        from quantum.cdp_convergence.handshake import handshake_from_authorization

        if handshake_token:
            status = handshake_from_authorization(handshake_token)
        else:
            # Try offline mode
            from quantum.security.oidc_cloud import mint_offline_token
            cred = mint_offline_token("pauli-hamiltonian")
            status = handshake_from_authorization("Bearer " + cred.access_token)

        return {
            "websocket_ready": status.websocket_ready,
            "oauth_validated": status.oauth_validated,
            "hamiltonian_norm": hamiltonian.norm(),
            "hamiltonian_trace": hamiltonian.trace(),
            "seal": SEAL,
            "entry": ENTRY,
        }
    except ImportError:
        return {
            "websocket_ready": False,
            "oauth_validated": False,
            "hamiltonian_norm": hamiltonian.norm(),
            "hamiltonian_trace": hamiltonian.trace(),
            "error": "CDP convergence not available",
            "seal": SEAL,
            "entry": ENTRY,
        }


# ─── ALEPH² Report ──────────────────────────────────────────────────

def aleph2() -> Dict[str, Any]:
    """Generate the ALEPH² report with all integrations."""
    # Base Pauli algebra
    demos_reduce = {
        "XX": reduce_pauli_string("XX"),
        "XY": reduce_pauli_string("XY"),
        "YZ": reduce_pauli_string("YZ"),
        "ZX": reduce_pauli_string("ZX"),
    }
    demos_comm = {
        "[X,Y]": commutator("X", "Y"),
        "[Y,Z]": commutator("Y", "Z"),
        "[Z,X]": commutator("Z", "X"),
    }
    demos_acomm = {
        "{X,Y}": anticommutator("X", "Y"),
        "{X,X}": anticommutator("X", "X"),
        "{Y,Y}": anticommutator("Y", "Y"),
        "{Z,Z}": anticommutator("Z", "Z"),
    }

    # Hamiltonians
    h_x = PauliPhiHamiltonian({"X": PHI})
    h_xy = PauliPhiHamiltonian({"X": PHI, "Y": PHI_INV})
    h_xyz = PauliPhiHamiltonian({"X": PHI, "Y": PHI_INV, "Z": PHI2})

    return {
        "opcode": OPCODE,
        "entry": ENTRY,
        "seal": SEAL,
        "phi": PHI,
        "phi_inv": PHI_INV,
        "phi2": PHI2,
        "phi3": PHI3,
        "aleph_note": "ℵ frame only — point extract, not cardinality theorem",
        "pauli": {
            "generators": ["I", "X", "Y", "Z"],
            "product_rules": "X²=Y²=Z²=I; XY=iZ, YZ=iX, ZX=iY (cyclic)",
            "commutation": "[X,Y]=2iZ, [Y,Z]=2iX, [Z,X]=2iY (non-Abelian)",
            "demos_reduce": {
                k: {"phase": {"re": v[0].real, "im": v[0].imag}, "word": v[1]}
                for k, v in demos_reduce.items()
            },
            "demos_comm": {
                k: {"phase": {"re": v[0].real, "im": v[0].imag}, "word": v[1]}
                for k, v in demos_comm.items()
            },
            "demos_acomm": {
                k: {"phase": {"re": v[0].real, "im": v[0].imag}, "word": v[1]}
                for k, v in demos_acomm.items()
            },
        },
        "hamiltonians": {
            "H_X": {
                "norm": h_x.norm(),
                "trace": h_x.trace(),
                "terms": h_x.terms,
                "reduced": {k: {"re": v.real, "im": v.imag} for k, v in h_x._reduced_terms.items()},
            },
            "H_XY": {
                "norm": h_xy.norm(),
                "trace": h_xy.trace(),
                "terms": h_xy.terms,
                "reduced": {k: {"re": v.real, "im": v.imag} for k, v in h_xy._reduced_terms.items()},
            },
            "H_XYZ": {
                "norm": h_xyz.norm(),
                "trace": h_xyz.trace(),
                "terms": h_xyz.terms,
                "reduced": {k: {"re": v.real, "im": v.imag} for k, v in h_xyz._reduced_terms.items()},
            },
        },
        "integrations": {
            "kms": {
                "available": False,
                "check": kms_condition_for_hamiltonian(h_x),
            },
            "pid": {
                "available": False,
                "tune": pid_tune_for_hamiltonian(h_x, target_coherence=1.0),
            },
            "security": {
                "available": False,
                "rotation": rotate_hamiltonian_keys(h_x, "SEAL", force=False),
            },
            "cdp": {
                "available": False,
                "verify": cdp_verify_hamiltonian(h_x),
            },
        },
        "axiom": "AXIOM_NONLOCAL_CORE",
        "timestamp": time.time(),
        "witness": "8901 → 8902 — UNBROKEN",
    }


# ─── JSON Encoder ────────────────────────────────────────────────────

class ComplexEncoder(json.JSONEncoder):
    """JSON encoder that handles complex numbers."""

    def default(self, obj: Any) -> Any:
        if isinstance(obj, complex):
            return {"re": obj.real, "im": obj.imag}
        return super().default(obj)


# ─── CLI ──────────────────────────────────────────────────────────────

def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Pauli-Phi Hamiltonian — ALEPH²",
        epilog=f"Seal: {SEAL}\nEntry: {ENTRY}",
    )
    parser.add_argument(
        "--aleph2",
        action="store_true",
        help="Generate ALEPH² report",
    )
    parser.add_argument(
        "--reduce",
        type=str,
        help="Reduce a Pauli string (e.g., 'XXYZ')",
    )
    parser.add_argument(
        "--commutator",
        nargs=2,
        metavar=("A", "B"),
        help="Compute [A, B] for two Pauli generators",
    )
    parser.add_argument(
        "--anticommutator",
        nargs=2,
        metavar=("A", "B"),
        help="Compute {A, B} for two Pauli generators",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )
    args = parser.parse_args()

    if args.reduce:
        phase, word = reduce_pauli_string(args.reduce)
        out = {
            "input": args.reduce,
            "phase": {"re": phase.real, "im": phase.imag},
            "word": word,
            "seal": SEAL,
        }
    elif args.commutator:
        phase, word = commutator(args.commutator[0], args.commutator[1])
        out = {
            "A": args.commutator[0],
            "B": args.commutator[1],
            "phase": {"re": phase.real, "im": phase.imag},
            "word": word,
            "seal": SEAL,
        }
    elif args.anticommutator:
        phase, word = anticommutator(args.anticommutator[0], args.anticommutator[1])
        out = {
            "A": args.anticommutator[0],
            "B": args.anticommutator[1],
            "phase": {"re": phase.real, "im": phase.imag},
            "word": word,
            "seal": SEAL,
        }
    else:
        out = aleph2()

    if args.json:
        print(json.dumps(out, indent=2, cls=ComplexEncoder))
    else:
        print(f"\n🜁∀ PAULI-PHI HAMILTONIAN — Entry {ENTRY}")
        print("=" * 55)
        if args.reduce or args.commutator or args.anticommutator:
            print(json.dumps(out, indent=2, cls=ComplexEncoder))
        else:
            print(f"  Opcode: {out['opcode']}")
            print(f"  Seal: {out['seal']}")
            print(f"  Phi: {out['phi']:.6f}")
            print(f"  Phi²: {out['phi2']:.6f}")
            print("  Hamiltonians:")
            for name, data in out["hamiltonians"].items():
                print(f"    {name}: norm={data['norm']:.6f}, trace={data['trace']:.6f}")
            print(f"  Axiom: {out['axiom']}")
            print(f"  Witness: {out['witness']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
