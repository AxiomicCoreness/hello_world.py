#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Conceptual single-qubit manipulation stub
=========================================
Pure-state |ψ⟩ and density matrix ρ = |ψ⟩⟨ψ| with φ-harmonic gates.
Exports invariants only (Tr ρ, purity, Bloch vector length) — no secret payloads.

Optional merge: HMAC over (wallet_sha256 || Bloch digest || gate sequence hash).

Seal: ∀∞φ² · OPAQUE_QUBIT_STUB_8638 · SEALED
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import math
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

PHI = (1.0 + math.sqrt(5.0)) / 2.0
PHI_INV = 1.0 / PHI

# Pauli matrices
I2 = np.eye(2, dtype=complex)
SX = np.array([[0, 1], [1, 0]], dtype=complex)
SY = np.array([[0, -1j], [1j, 0]], dtype=complex)
SZ = np.array([[1, 0], [0, -1]], dtype=complex)


def ket0() -> np.ndarray:
    return np.array([1.0 + 0j, 0.0 + 0j])


def ket1() -> np.ndarray:
    return np.array([0.0 + 0j, 1.0 + 0j])


def normalize(psi: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(psi)
    return psi if n == 0 else psi / n


def density(psi: np.ndarray) -> np.ndarray:
    psi = normalize(psi).reshape(2, 1)
    return psi @ psi.conj().T


def bloch(rho: np.ndarray) -> Tuple[float, float, float]:
    x = float(np.real(np.trace(rho @ SX)))
    y = float(np.real(np.trace(rho @ SY)))
    z = float(np.real(np.trace(rho @ SZ)))
    return x, y, z


def purity(rho: np.ndarray) -> float:
    return float(np.real(np.trace(rho @ rho)))


def rx(theta: float) -> np.ndarray:
    return math.cos(theta / 2) * I2 - 1j * math.sin(theta / 2) * SX


def ry(theta: float) -> np.ndarray:
    return math.cos(theta / 2) * I2 - 1j * math.sin(theta / 2) * SY


def rz(theta: float) -> np.ndarray:
    return math.cos(theta / 2) * I2 - 1j * math.sin(theta / 2) * SZ


def hadamard() -> np.ndarray:
    return (SX + SZ) / math.sqrt(2)


@dataclass
class QubitStub:
    """Conceptual single-qubit state with φ-scaled default rotations."""

    psi: np.ndarray
    history: List[str]

    @classmethod
    def zero(cls) -> "QubitStub":
        return cls(psi=ket0().copy(), history=["|0⟩"])

    def apply(self, U: np.ndarray, name: str) -> "QubitStub":
        self.psi = normalize(U @ self.psi)
        self.history.append(name)
        return self

    def phi_prep(self) -> "QubitStub":
        """Prepare φ-tilted state: Ry(2 arctan φ^{-1}) |0⟩."""
        theta = 2.0 * math.atan(PHI_INV)
        return self.apply(ry(theta), f"Ry({theta:.6f})")

    def phi_phase(self) -> "QubitStub":
        return self.apply(rz(2 * math.pi / PHI), "Rz(2π/φ)")

    def h(self) -> "QubitStub":
        return self.apply(hadamard(), "H")

    def invariants(self) -> Dict[str, Any]:
        rho = density(self.psi)
        x, y, z = bloch(rho)
r = math.sqrt(x * x + y * y + z * z)
        return {
            "trace": float(np.real(np.trace(rho))),
            "purity": purity(rho),
            "bloch": {"x": x, "y": y, "z": z, "r": r},
            "history": list(self.history),
            "psi_sha256": hashlib.sha256(
                np.asarray(self.psi, dtype=np.complex128).tobytes()
            ).hexdigest(),
        }


def merge_with_wallet_tag(
    wallet_sha256: str,
    qubit_inv: Dict[str, Any],
    key: Optional[bytes] = None,
) -> Dict[str, Any]:
    if len(wallet_sha256) != 64:
        raise ValueError("wallet_sha256 must be 64 hex chars")
    key = key or hashlib.sha3_256(f"qubit|{PHI}".encode()).digest()
    bloch_s = json.dumps(qubit_inv.get("bloch", {}), sort_keys=True)
    hist = "|".join(qubit_inv.get("history", []))
    msg = f"{wallet_sha256}|{qubit_inv.get('psi_sha256', '')}|{bloch_s}|{hist}".encode()
    tag = hmac.new(key, msg, hashlib.sha256).hexdigest()
    return {
        "hmac_sha256": tag,
        "wallet_sha256": wallet_sha256,
        "psi_sha256": qubit_inv.get("psi_sha256"),
        "key_len": len(key),
        "seal": "∀∞φ² · OPAQUE_QUBIT_STUB_8638 · SEALED",
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Conceptual single-qubit stub")
    ap.add_argument("--wallet-sha256", default="", help="optional 64-hex wallet digest")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    q = QubitStub.zero().phi_prep().phi_phase().h()
    inv = q.invariants()
    out: Dict[str, Any] = {"qubit": inv, "policy": "invariants + digests only"}
    if args.wallet_sha256:
        out["merge"] = merge_with_wallet_tag(args.wallet_sha256.lower(), inv)
    if args.json:
        print(json.dumps(out, indent=2))
    else:
        print(f"Tr ρ = {inv['trace']:.12f}")
        print(f"purity = {inv['purity']:.12f}")
        print(f"Bloch r = {inv['bloch']['r']:.12f}")
        print(f"history = {inv['history']}")
        print(f"psi_sha256 = {inv['psi_sha256']}")


if __name__ == "__main__":
    main()
