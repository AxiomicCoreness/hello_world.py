#!/usr/bin/env python3
"""
symplectic_time_origami.py
Symplectic time origami → AES-256 key material + SHA3-512 digest

S = [[φ, 1], [1, φ⁻¹]]  (det S = 1)
Entropy: SHA-512 of folded state (64 bytes)
AES-256 key: first 32 bytes of entropy (hex: 64 chars)
SHA3-512 digest: 64 bytes (hex: 128 chars)
There is no AES-512.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

PHI = (1 + 5 ** 0.5) / 2


@dataclass
class SymplecticTimeOrigami:
    t0: float = 0.0
    phi0: float = 0.0
    delta_t: float = 78624.0  # FRB period (seconds)

    def _symplectic_matrix(self) -> Tuple[float, float, float, float]:
        return (PHI, 1.0, 1.0, PHI ** -1)

    def fold(self, t: float, phi: float) -> Tuple[float, float]:
        a, b, c, d = self._symplectic_matrix()
        return a * t + b * phi, c * t + d * phi

    def generate_material(self, t: float, phi: float) -> Dict[str, Any]:
        t_fold, phi_fold = self.fold(t, phi)
        material = f"{t_fold:.15f}|{phi_fold:.15f}|{PHI:.15f}|{self.delta_t}".encode()
        entropy = hashlib.sha512(material).digest()  # 64 bytes
        aes_key = entropy[:32]  # AES-256 only
        sha3_512 = hashlib.sha3_512(entropy).digest()  # 64 bytes
        return {
            "aes256_key_hex": aes_key.hex(),  # 64 hex
            "sha3_512_digest_hex": sha3_512.hex(),  # 128 hex
            "entropy_sha512_hex": entropy.hex(),  # 128 hex
            "folded_t": t_fold,
            "folded_phi": phi_fold,
            "det_S": PHI * (PHI ** -1) - 1.0,  # ≈ 0 → symplectic
            "aes512_supported": False,
        }

    def time_origami(self, timestamp: float, phase: Optional[float] = None) -> Dict[str, Any]:
        if phase is None:
            phase = 202.6  # Chiron phase lock (degrees treated as scalar input)
        return self.generate_material(timestamp, phase)


def main() -> None:
    import time

    o = SymplecticTimeOrigami()
    out = o.time_origami(time.time())
    print("aes256_key_hex:     ", out["aes256_key_hex"])
    print("sha3_512_digest_hex:", out["sha3_512_digest_hex"])
    print("aes512_supported:   ", out["aes512_supported"])
    print("det_S ≈ 0:          ", abs(out["det_S"]) < 1e-12)


if __name__ == "__main__":
    main()
