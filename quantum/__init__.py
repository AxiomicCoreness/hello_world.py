"""Quantum subsystem — optional exports (soft imports)."""

__all__ = []

try:
    from .pauli_phi_hamiltonian import (
        PauliPhiHamiltonian,
        hamiltonian_trace,
        verify_trace_identity,
    )

    __all__ += ["PauliPhiHamiltonian", "hamiltonian_trace", "verify_trace_identity"]
except Exception:
    pass
