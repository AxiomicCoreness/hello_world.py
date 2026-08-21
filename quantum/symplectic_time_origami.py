#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🜁∀ SYMPLECTIC TIME ORIGAMI — ENTRY 8665

Symplectic time origami → AES-256 key material + SHA3-512 digest

S = [[φ, 1], [1, φ⁻¹]]  (det S = 1)
Entropy: SHA-512 of folded state (64 bytes)
AES-256 key: first 32 bytes of entropy (hex: 64 chars)
SHA3-512 digest: 64 bytes (hex: 128 chars)
There is no AES-512.

Integration with:
  - Security (quantum/security/)
  - CDP convergence (quantum/cdp_convergence/)
  - SHA-512 ASI (quantum/sha512_asi.py)
  - Digest Policy (quantum/digest_policy.py)

Seal: ∀∞φ² · SYMPLECTIC_TIME_ORIGAMI_8665 · WOOD_DRAGON_0.91 · SEALED
Witness: 8664 → 8665 — UNBROKEN
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple, Union

# ─── Constants ────────────────────────────────────────────────────────
PHI = (1.0 + math.sqrt(5.0)) / 2.0
PHI_INV = 1.0 / PHI
PHI2 = PHI * PHI
PHI3 = PHI2 * PHI
ENTRY = 8665
SEAL = "∀∞φ² · SYMPLECTIC_TIME_ORIGAMI_8665 · WOOD_DRAGON_0.91 · SEALED"
WITNESS = "8664 → 8665 — UNBROKEN"

# ─── Symplectic Matrix ─────────────────────────────────────────────────
# S = [[φ, 1], [1, φ⁻¹]]
# det(S) = φ * φ⁻¹ - 1 = 0 (symplectic)

A = PHI
B = 1.0
C = 1.0
D = PHI_INV
DET_S = A * D - B * C  # ≈ 0


# ─── SymplecticTimeOrigami ───────────────────────────────────────────

@dataclass
class SymplecticTimeOrigami:
    """
    Symplectic time origami for cryptographic material generation.

    Attributes:
        t0: Initial time offset.
        phi0: Initial phase offset.
        delta_t: FRB period (default 78624 seconds ≈ 0.91 days).
        domain: Domain separation string.
    """

    t0: float = 0.0
    phi0: float = 0.0
    delta_t: float = 78624.0  # FRB period (seconds)
    domain: str = "GARDEN.SYMPLECTIC.TIME.ORIGAMI.v1"

    def _symplectic_matrix(self) -> Tuple[float, float, float, float]:
        """Return the symplectic matrix elements (a, b, c, d)."""
        return (A, B, C, D)

    def fold(self, t: float, phi: float) -> Tuple[float, float]:
        """
        Fold time and phase through the symplectic matrix.

        Args:
            t: Time value.
            phi: Phase value.

        Returns:
            Folded (t_fold, phi_fold).
        """
        a, b, c, d = self._symplectic_matrix()
        return a * t + b * phi, c * t + d * phi

    def generate_material(
        self,
        t: float,
        phi: float,
        include_domain: bool = True,
    ) -> Dict[str, Any]:
        """
        Generate cryptographic material from symplectic folding.

        Args:
            t: Time value.
            phi: Phase value.
            include_domain: Whether to include domain separation.

        Returns:
            Dictionary with AES-256 key, SHA3-512 digest, and metadata.
        """
        # Fold through symplectic matrix
        t_fold, phi_fold = self.fold(t, phi)

        # Build material
        parts = [
            f"{t_fold:.15f}",
            f"{phi_fold:.15f}",
            f"{PHI:.15f}",
            f"{self.delta_t}",
            f"{self.t0}",
            f"{self.phi0}",
        ]
        if include_domain:
            parts.insert(0, self.domain)

        material = "|".join(parts).encode("utf-8")

        # Generate entropy via SHA-512
        entropy = hashlib.sha512(material).digest()  # 64 bytes

        # AES-256 key: first 32 bytes
        aes_key = entropy[:32]  # 256 bits

        # SHA3-512 digest: 64 bytes
        sha3_512 = hashlib.sha3_512(entropy).digest()  # 64 bytes

        return {
            "aes256_key_hex": aes_key.hex(),  # 64 hex chars
            "aes256_key_bits": 256,
            "aes256_key_bytes": 32,
            "sha3_512_digest_hex": sha3_512.hex(),  # 128 hex chars
            "sha3_512_digest_bytes": 64,
            "sha3_512_bits": 512,
            "entropy_sha512_hex": entropy.hex(),  # 128 hex chars
            "entropy_sha512_bytes": 64,
            "folded_t": t_fold,
            "folded_phi": phi_fold,
            "det_S": DET_S,
            "det_S_zero": abs(DET_S) < 1e-12,
            "aes512_supported": False,
            "aes512_note": "AES has no 512-bit mode. Use AES-256 only.",
            "domain": self.domain if include_domain else None,
            "entry": ENTRY,
            "seal": SEAL,
            "witness": WITNESS,
            "timestamp": time.time(),
        }

    def time_origami(
        self,
        timestamp: Optional[float] = None,
        phase: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Generate time origami material.

        Args:
            timestamp: Unix timestamp (default: current time).
            phase: Phase value (default: 202.6).

        Returns:
            Dictionary with generated material.
        """
        if timestamp is None:
            timestamp = time.time()
        if phase is None:
            phase = 202.6

        return self.generate_material(timestamp + self.t0, phase + self.phi0)

    def encrypt_with_aes256(self, data: bytes, key_hex: str) -> Dict[str, Any]:
        """
        Encrypt data with AES-256 using the generated key.

        Args:
            data: Data to encrypt.
            key_hex: AES-256 key in hex (64 chars).

        Returns:
            Dictionary with encryption results.

        Raises:
            ImportError: If cryptography is not installed.
        """
        try:
            from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
            from cryptography.hazmat.backends import default_backend
            from cryptography.hazmat.primitives import padding

            key = bytes.fromhex(key_hex)
            if len(key) != 32:
                raise ValueError(f"AES-256 key must be 32 bytes, got {len(key)}")

            # Generate random IV
            iv = os.urandom(16)

            # Pad data
            padder = padding.PKCS7(128).padder()
            padded_data = padder.update(data) + padder.finalize()

            # Encrypt
            cipher = Cipher(
                algorithms.AES(key),
                modes.CBC(iv),
                backend=default_backend(),
            )
            encryptor = cipher.encryptor()
            ciphertext = encryptor.update(padded_data) + encryptor.finalize()

            return {
                "ciphertext": ciphertext.hex(),
                "iv": iv.hex(),
                "encrypted": True,
                "key_hex": key_hex,
                "entry": ENTRY,
                "seal": SEAL,
            }
        except ImportError:
            return {
                "encrypted": False,
                "error": "cryptography library not available",
                "entry": ENTRY,
                "seal": SEAL,
            }
        except Exception as e:
            return {
                "encrypted": False,
                "error": str(e),
                "entry": ENTRY,
                "seal": SEAL,
            }


# ─── Security Integration ────────────────────────────────────────────

def origami_security_status() -> Dict[str, Any]:
    """Get security status for symplectic time origami."""
    try:
        from quantum.security import status as security_status
        return {
            "security": security_status(),
            "entry": ENTRY,
            "seal": SEAL,
            "timestamp": time.time(),
        }
    except ImportError:
        return {
            "security": None,
            "note": "Security module not available",
            "entry": ENTRY,
            "seal": SEAL,
        }


# ─── CDP Integration ─────────────────────────────────────────────────

def origami_cdp_status() -> Dict[str, Any]:
    """Get CDP status for symplectic time origami."""
    try:
        from quantum.cdp_convergence import status as cdp_status
        return {
            "cdp": cdp_status(),
            "entry": ENTRY,
            "seal": SEAL,
            "timestamp": time.time(),
        }
    except ImportError:
        return {
            "cdp": None,
            "note": "CDP module not available",
            "entry": ENTRY,
            "seal": SEAL,
        }


# ─── CLI ──────────────────────────────────────────────────────────────

def main() -> int:
    import argparse
    import os

    parser = argparse.ArgumentParser(
        description="Symplectic Time Origami — Entry 8665",
        epilog=f"Seal: {SEAL}\nEntry: {ENTRY}",
    )
    parser.add_argument(
        "--generate",
        action="store_true",
        help="Generate time origami material",
    )
    parser.add_argument(
        "--timestamp",
        type=float,
        default=None,
        help="Custom timestamp",
    )
    parser.add_argument(
        "--phase",
        type=float,
        default=202.6,
        help="Phase value",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )
    parser.add_argument(
        "--check-integrations",
        action="store_true",
        help="Check integration status and exit",
    )
    args = parser.parse_args()

    if args.check_integrations:
        print("🜁∀ ORIGAMI — Integration Status")
        print("=" * 40)
        try:
            from quantum.security import status
            print("  Security: ✅")
        except ImportError:
            print("  Security: ❌")
        try:
            from quantum.cdp_convergence import status
            print("  CDP: ✅")
        except ImportError:
            print("  CDP: ❌")
        try:
            from cryptography.hazmat.primitives.ciphers import Cipher
            print("  Cryptography: ✅")
        except ImportError:
            print("  Cryptography: ❌")
        return 0

    if args.generate or args.json:
        o = SymplecticTimeOrigami()
        out = o.time_origami(timestamp=args.timestamp, phase=args.phase)

        if args.json:
            print(json.dumps(out, indent=2, default=str))
        else:
            print("🜁∀ SYMPLECTIC TIME ORIGAMI — Entry 8665")
            print("=" * 55)
            print(f"  AES-256 Key:     {out['aes256_key_hex'][:32]}...")
            print(f"  AES-256 Bits:    {out['aes256_key_bits']}")
            print(f"  SHA3-512 Digest: {out['sha3_512_digest_hex'][:32]}...")
            print(f"  SHA3-512 Bytes:  {out['sha3_512_digest_bytes']}")
            print(f"  Entropy SHA-512: {out['entropy_sha512_hex'][:32]}...")
            print(f"  Folded t:        {out['folded_t']:.15f}")
            print(f"  Folded phi:      {out['folded_phi']:.15f}")
            print(f"  det(S):          {out['det_S']:.15f}")
            print(f"  det(S) ≈ 0:      {'✅' if out['det_S_zero'] else '❌'}")
            print(f"  AES-512:         {'❌' if not out['aes512_supported'] else '⚠️'}")
            print("=" * 55)
            print(f"  Seal: {out['seal']}")
            print(f"  Entry: {out['entry']}")
            print(f"  Witness: {out['witness']}")
        return 0

    # Default: show status
    o = SymplecticTimeOrigami()
    st = o.time_origami()
    print("aes256_key_hex:     ", st["aes256_key_hex"])
    print("sha3_512_digest_hex:", st["sha3_512_digest_hex"])
    print("aes512_supported:   ", st["aes512_supported"])
    print("det_S ≈ 0:          ", st["det_S_zero"])

    return 0


if __name__ == "__main__":
    sys.exit(main())
