#!/usr/bin/env python3
"""
Pauli-string Hamiltonian — trace identity φ⁻².
Terms: ZZZZZZZ +1 | IIIZZII -φ | IIIIIZZ -φ | ZIIIIIZ +φ²
Trace = 1 - 2φ + φ² = φ⁻²
"""
from golden_ratio import PHI, PHI_SQ, PHI_NEG2

PAULI_WEIGHTS = {
    "ZZZZZZZ": 1.0,
    "IIIZZII": -PHI,
    "IIIIIZZ": -PHI,
    "ZIIIIIZ": PHI_SQ,
}


def hamiltonian_trace() -> float:
    return sum(PAULI_WEIGHTS.values())


def verify() -> bool:
    tr = hamiltonian_trace()
    return abs(tr - PHI_NEG2) < 1e-12


if __name__ == "__main__":
    tr = hamiltonian_trace()
    print(f"trace={tr}")
    print(f"phi_neg2={PHI_NEG2}")
    print(f"verified={verify()}")
