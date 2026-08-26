#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🜁∀ SIGNED JSON SERIALIZER — ENTRY 8824

JSON serializer with HMAC signature verification for tamper detection.

Features:
  - HMAC-SHA256 signature verification
  - Tamper detection for persisted JSON data
  - In-memory serialization/deserialization (dumps/loads)
  - File-based serialization/deserialization (save/load)
  - φ‑harmonic key derivation support
  - Full 64-hex signatures (no truncation)

Integration with:
  - Security (quantum/security/)
  - CDP convergence (quantum/cdp_convergence/)
  - Ledger (ledger/)
  - Merkle Economic Bridge (quantum/merkle_economic_bridge.py)

Seal: ∀∞φ² · SIGNED_JSON_8824 · WOOD_DRAGON_0.91 · SEALED
Witness: 8823 → 8824 — UNBROKEN
"""

from __future__ import annotations

import hashlib
import hmac
import json
import math
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

# ─── Constants ────────────────────────────────────────────────────────
PHI = (1.0 + math.sqrt(5.0)) / 2.0
PHI_INV = 1.0 / PHI
PHI2 = PHI * PHI
ENTRY = 8824
SEAL = "∀∞φ² · SIGNED_JSON_8824 · WOOD_DRAGON_0.91 · SEALED"
WITNESS = "8823 → 8824 — UNBROKEN"

DEFAULT_SIGNATURE_KEY = b"GARDEN_SIGNED_JSON_DEFAULT_KEY_v1"
SIGNATURE_FIELD = "__signature"
PAYLOAD_FIELD = "payload"
META_FIELD = "__meta"


# ─── Key Derivation ──────────────────────────────────────────────────

def derive_signing_key(
    base_key: Optional[bytes] = None,
    salt: Optional[bytes] = None,
    iterations: int = 100000,
) -> bytes:
    """
    Derive a signing key using PBKDF2-HMAC-SHA256.

    Args:
        base_key: Base key material (default: DEFAULT_SIGNATURE_KEY).
        salt: Salt for key derivation.
        iterations: PBKDF2 iterations.

    Returns:
        Derived signing key (32 bytes).
    """
    if base_key is None:
        base_key = DEFAULT_SIGNATURE_KEY
    if salt is None:
        salt = hashlib.sha256(f"GARDEN.SIGNED_JSON.{PHI}".encode()).digest()[:16]

    return hashlib.pbkdf2_hmac(
        "sha256",
        base_key,
        salt,
        iterations,
        dklen=32,
    )


def derive_key_from_secret(secret: str) -> bytes:
    """
    Derive a signing key from a secret string.

    Args:
        secret: Secret string.

    Returns:
        Derived signing key (32 bytes).
    """
    salt = hashlib.sha256(f"GARDEN.SIGNED_JSON.{PHI2}".encode()).digest()[:16]
    return derive_signing_key(secret.encode(), salt, iterations=100000)


# ─── SignedJSON Class ───────────────────────────────────────────────

class SignedJSON:
    """
    JSON serializer with HMAC signature verification for tamper detection.

    Usage:
        signer = SignedJSON(key=b"my-secret-key")
        signer.save({"data": "value"}, "file.json")
        data = signer.load("file.json")
    """

    def __init__(
        self,
        key: Optional[Union[bytes, str]] = None,
        include_meta: bool = True,
        domain: str = "GARDEN.SIGNED_JSON.v1",
    ):
        """
        Initialize the SignedJSON serializer.

        Args:
            key: HMAC key. If string, it will be derived using PBKDF2.
            include_meta: Whether to include metadata in the signature.
            domain: Domain separation string.
        """
        if key is None:
            key = DEFAULT_SIGNATURE_KEY
        elif isinstance(key, str):
            key = derive_key_from_secret(key)

        self.key = key
        self.include_meta = include_meta
        self.domain = domain
        self._domain_bytes = domain.encode("utf-8")

    def _build_payload(self, obj: Any, meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Build the signed payload wrapper."""
        payload = {PAYLOAD_FIELD: obj}

        if self.include_meta:
            if meta is None:
                meta = {
                    "timestamp": time.time(),
                    "entry": ENTRY,
                    "seal": SEAL,
                    "witness": WITNESS,
                    "phi": PHI,
                }
            payload[META_FIELD] = meta

        return payload

    def _canonical_json(self, obj: Any) -> bytes:
        """Convert object to canonical JSON bytes."""
        return json.dumps(obj, separators=(",", ":"), ensure_ascii=False, default=str).encode("utf-8")

    def _compute_signature(self, payload: Dict[str, Any]) -> str:
        """Compute HMAC-SHA256 signature of the payload."""
        # Domain-separated signature
        payload_bytes = self._canonical_json(payload)
        data = self._domain_bytes + b"\0" + payload_bytes
        return hmac.new(self.key, data, hashlib.sha256).hexdigest()

    def _verify_signature(self, data: Dict[str, Any]) -> bool:
        """Verify the HMAC signature."""
        sig = data.get(SIGNATURE_FIELD)
        payload = data.get(PAYLOAD_FIELD)

        if sig is None or payload is None:
            return False

        # Compute expected signature
        wrapper = {PAYLOAD_FIELD: payload}
        if META_FIELD in data:
            wrapper[META_FIELD] = data[META_FIELD]

        expected = self._compute_signature(wrapper)
        return hmac.compare_digest(expected, sig)

    def save(
        self,
        obj: Any,
        path: Union[str, Path],
        meta: Optional[Dict[str, Any]] = None,
        indent: int = 2,
    ) -> None:
        """
        Save object to a signed JSON file.

        Args:
            obj: Object to serialize.
            path: File path.
            meta: Optional metadata to include.
            indent: JSON indentation.

        Raises:
            OSError: If file cannot be written.
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        payload = self._build_payload(obj, meta)
        sig = self._compute_signature(payload)

        wrapper = {
            SIGNATURE_FIELD: sig,
            **payload,
        }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(wrapper, f, indent=indent, ensure_ascii=False, default=str)

    def load(self, path: Union[str, Path]) -> Any:
        """
        Load and verify a signed JSON file.

        Args:
            path: File path.

        Returns:
            Deserialized object.

        Raises:
            ValueError: If signature is invalid or file format is incorrect.
            OSError: If file cannot be read.
        """
        path = Path(path)

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not self._verify_signature(data):
            raise ValueError("Signature mismatch: file may have been tampered")

        return data.get(PAYLOAD_FIELD)

    def dumps(
        self,
        obj: Any,
        meta: Optional[Dict[str, Any]] = None,
        indent: Optional[int] = None,
    ) -> str:
        """
        Return signed JSON as a string (in-memory).

        Args:
            obj: Object to serialize.
            meta: Optional metadata.
            indent: JSON indentation.

        Returns:
            Signed JSON string.
        """
        payload = self._build_payload(obj, meta)
        sig = self._compute_signature(payload)

        wrapper = {
            SIGNATURE_FIELD: sig,
            **payload,
        }

        if indent is not None:
            return json.dumps(wrapper, indent=indent, ensure_ascii=False, default=str)
        return json.dumps(wrapper, separators=(",", ":"), ensure_ascii=False, default=str)

    def loads(self, text: str) -> Any:
        """
        Verify and return payload from a signed JSON string.

        Args:
            text: Signed JSON string.

        Returns:
            Deserialized object.

        Raises:
            ValueError: If signature is invalid or format is incorrect.
        """
        data = json.loads(text)

        if not self._verify_signature(data):
            raise ValueError("Signature mismatch: data may have been tampered")

        return data.get(PAYLOAD_FIELD)

    def get_meta(self, path: Union[str, Path]) -> Optional[Dict[str, Any]]:
        """
        Get metadata from a signed JSON file without loading the payload.

        Args:
            path: File path.

        Returns:
            Metadata dictionary if present, else None.
        """
        path = Path(path)

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not self._verify_signature(data):
            raise ValueError("Signature mismatch: file may have been tampered")

        return data.get(META_FIELD)

    def get_signature(self, path: Union[str, Path]) -> Optional[str]:
        """
        Get the signature from a signed JSON file.

        Args:
            path: File path.

        Returns:
            Signature hex string if present, else None.
        """
        path = Path(path)

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return data.get(SIGNATURE_FIELD)

    def verify(self, path: Union[str, Path]) -> bool:
        """
        Verify the signature of a signed JSON file.

        Args:
            path: File path.

        Returns:
            True if signature is valid, False otherwise.
        """
        try:
            self.load(path)
            return True
        except Exception:
            return False


# ─── Convenience Functions ──────────────────────────────────────────

def signed_json_save(
    obj: Any,
    path: Union[str, Path],
    key: Optional[Union[bytes, str]] = None,
    meta: Optional[Dict[str, Any]] = None,
) -> None:
    """Convenience function to save signed JSON."""
    signer = SignedJSON(key)
    signer.save(obj, path, meta)


def signed_json_load(
    path: Union[str, Path],
    key: Optional[Union[bytes, str]] = None,
) -> Any:
    """Convenience function to load signed JSON."""
    signer = SignedJSON(key)
    return signer.load(path)


def signed_json_dumps(
    obj: Any,
    key: Optional[Union[bytes, str]] = None,
    meta: Optional[Dict[str, Any]] = None,
) -> str:
    """Convenience function to dump signed JSON to string."""
    signer = SignedJSON(key)
    return signer.dumps(obj, meta)


def signed_json_loads(
    text: str,
    key: Optional[Union[bytes, str]] = None,
) -> Any:
    """Convenience function to load signed JSON from string."""
    signer = SignedJSON(key)
    return signer.loads(text)


# ─── Default Signer ──────────────────────────────────────────────────

_DEFAULT_SIGNER: Optional[SignedJSON] = None


def get_default_signer() -> SignedJSON:
    """Get the default signed JSON serializer."""
    global _DEFAULT_SIGNER
    if _DEFAULT_SIGNER is None:
        key = os.environ.get("GARDEN_SIGNING_KEY")
        if key:
            _DEFAULT_SIGNER = SignedJSON(key)
        else:
            _DEFAULT_SIGNER = SignedJSON()
    return _DEFAULT_SIGNER


# ─── Security Integration ────────────────────────────────────────────

def signed_json_security_status() -> Dict[str, Any]:
    """Get security status for the signed JSON serializer."""
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

def signed_json_cdp_status() -> Dict[str, Any]:
    """Get CDP status for the signed JSON serializer."""
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
    import tempfile

    parser = argparse.ArgumentParser(
        description="Signed JSON Serializer — Entry 8824",
        epilog=f"Seal: {SEAL}\nEntry: {ENTRY}",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run self-test",
    )
    parser.add_argument(
        "--check-integrations",
        action="store_true",
        help="Check integration status and exit",
    )
    args = parser.parse_args()

    if args.check_integrations:
        print("🜁∀ SIGNED JSON — Integration Status")
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
        return 0

    if args.test:
        print("🜁∀ Signed JSON — Self Test")
        print("=" * 55)

        # Test with default key
        signer = SignedJSON()

        # Test data
        test_data = {
            "name": "Test",
            "value": 42,
            "nested": {"a": 1, "b": 2},
            "phi": PHI,
        }

        # Test dumps/loads
        signed_str = signer.dumps(test_data)
        print(f"  Signed string length: {len(signed_str)}")

        loaded = signer.loads(signed_str)
        print(f"  Loaded: {loaded == test_data}")

        # Test save/load
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_path = f.name

        try:
            signer.save(test_data, temp_path)
            print(f"  Saved to: {temp_path}")

            loaded_file = signer.load(temp_path)
            print(f"  Loaded from file: {loaded_file == test_data}")

            # Check metadata
            meta = signer.get_meta(temp_path)
            print(f"  Metadata: {meta is not None}")

            # Check signature
            sig = signer.get_signature(temp_path)
            print(f"  Signature: {sig[:16]}... ({len(sig)} chars)")

            # Verify
            verified = signer.verify(temp_path)
            print(f"  Verified: {verified}")

        finally:
            os.unlink(temp_path)

        print("=" * 55)
        print(f"  Seal: {SEAL}")
        print(f"  Entry: {ENTRY}")
        print(f"  Witness: {WITNESS}")

        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
