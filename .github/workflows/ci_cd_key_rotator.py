#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ci_cd_key_rotator.py — Sovereign Key Rotator with φ‑harmonic PRNG

This module provides a sovereign key rotation system using HMAC-SHA3-256
derivation with a φ‑harmonic pseudo‑random generator. It supports two
output formats: Flask128 (32 hex chars) and URL‑safe Base64.

Security Headers (CORS, CSP, HSTS, etc.) are NOT enforced by this script,
as it is a CLI/backend utility. They are enforced at the service layer in
port380_mcp.py (FastAPI middleware). The GitHub Actions workflow includes
a verification step to ensure those headers are present.

Seal: ∀∞φ² · KEY_ROTATION_INTEGRATED · 632_SEALED
"""

import os
import json
import time
import hashlib
import hmac
import base64
import math
import boto3
import secrets
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

# ─── CONSTANTS ────────────────────────────────────────────────────────────────
PHI = (1 + math.sqrt(5)) / 2
PHI_INV = 1 / PHI
SEAL = "∀∞φ² · KEY_ROTATION_INTEGRATED · 632_SEALED"


class PhiHarmonicPRNG:
    """φ-harmonic pseudo-random number generator."""

    def __init__(self, seed: bytes):
        self.state = int.from_bytes(hashlib.sha3_256(seed).digest()[:8], 'big') / (2**64)
        self.counter = 0

    def random(self) -> float:
        self.state = (self.state + PHI) % 1.0
        self.counter += 1
        return (self.state + self.counter * PHI_INV) % 1.0

    def randbytes(self, n: int) -> bytes:
        result = bytearray()
        while len(result) < n:
            val = int(self.random() * (2**56))
            result.extend(val.to_bytes(7, 'big'))
        return bytes(result[:n])


class SovereignKeyRotator:
    """φ-harmonic key rotator with HMAC-SHA3-256 derivation and dual encoding."""

    def __init__(self, master_seed: bytes):
        self.master_seed = master_seed
        self.prng = PhiHarmonicPRNG(master_seed)
        self.rotation_count = 0
        self.key_history: List[Dict[str, Any]] = []

    def _derive_key(self, index: int) -> bytes:
        message = f"{self.master_seed.hex()}:{index}:{PHI}".encode()
        return hmac.new(self.master_seed, message, hashlib.sha3_256).digest()

    def _encode_base64(self, key_bytes: bytes) -> str:
        """Encode key as URL‑safe base64 (standard format)."""
        return base64.urlsafe_b64encode(key_bytes).decode('ascii').rstrip('=')

    def _encode_flask128(self, key_bytes: bytes) -> str:
        """Encode key as Flask128 hex token (32 hex chars = 128 bits)."""
        return key_bytes[:16].hex()

    def _encode_key(self, key_bytes: bytes, fmt: str = "flask128") -> str:
        """
        Encode derived key in specified format.

        Args:
            key_bytes: Raw key bytes (32 bytes from HMAC-SHA3-256)
            fmt: "base64" (standard) or "flask128" (hex, 32 chars)

        Returns:
            Encoded key string
        """
        if fmt == "flask128":
            return self._encode_flask128(key_bytes)
        else:
            return self._encode_base64(key_bytes)

    def rotate(self, fmt: str = "flask128") -> Dict[str, Any]:
        """
        Perform key rotation.

        Args:
            fmt: Output format ("base64" or "flask128")

        Returns:
            Dict containing the new key and rotation metadata
        """
        self.rotation_count += 1
        key_bytes = self._derive_key(self.rotation_count)
        key = self._encode_key(key_bytes, fmt)

        # Generate a secure nonce for Flask compatibility
        nonce = secrets.token_hex(16)

        entry = {
            'index': self.rotation_count,
            'key_hash': hashlib.sha3_256(key.encode()).hexdigest()[:16],
            'key_format': fmt,
            'nonce': nonce,
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'seal': SEAL,
            'witness': f"{self.rotation_count-1} → {self.rotation_count} — UNBROKEN"
        }

        self.key_history.append(entry)

        return {
            'key': key,
            'metadata': entry
        }

    def get_current_key(self) -> Optional[str]:
        """Get the current key (if any). Note: actual key is not stored."""
        return None

    def get_current_metadata(self) -> Optional[Dict[str, Any]]:
        """Get the metadata of the current key."""
        if not self.key_history:
            return None
        return self.key_history[-1]


class AWSSecretsManager:
    """AWS SecretsManager interface for sovereign key storage."""

    def __init__(self, secret_name: str, region: str = "us-east-1"):
        self.secret_name = secret_name
        self.region = region
        self.client = boto3.client('secretsmanager', region_name=region)

    def load_state(self) -> Optional[Dict[str, Any]]:
        try:
            response = self.client.get_secret_value(SecretId=self.secret_name)
            return json.loads(response['SecretString'])
        except self.client.exceptions.ResourceNotFoundException:
            return None

    def save_state(self, state: Dict[str, Any]) -> None:
        self.client.put_secret_value(
            SecretId=self.secret_name,
            SecretString=json.dumps(state)
        )


def rotate_keys(
    secret_name: str = "sovereign-hamiltonian-hmac-632",
    region: str = "us-east-1",
    force: bool = False,
    count: int = 1,
    key_format: str = "flask128"
) -> Dict[str, Any]:
    """
    Main rotation function for GitHub Actions workflow.

    Args:
        secret_name: AWS Secrets Manager secret name
        region: AWS region
        force: Force rotation even if not due
        count: Number of rotations to perform
        key_format: "base64" or "flask128"

    Returns:
        Dict with rotation results and GitHub Actions outputs.
    """
    sm = AWSSecretsManager(secret_name, region)
    state = sm.load_state()

    if state and 'master_seed' in state:
        master_seed = bytes.fromhex(state['master_seed'])
        rotator = SovereignKeyRotator(master_seed)
        rotator.rotation_count = state.get('rotation_count', 0)
        rotator.key_history = state.get('key_history', [])
    else:
        master_seed = os.urandom(32)
        rotator = SovereignKeyRotator(master_seed)

    new_keys = []
    for i in range(count):
        if force or i > 0 or state is None:
            result = rotator.rotate(fmt=key_format)
            new_keys.append(result['key'])
            metadata = result['metadata']
            print(f'  ✅ Rotation {metadata["index"]}: {metadata["key_hash"]}... ({key_format})')

    # Store only metadata, not the key itself
    new_state = {
        'master_seed': master_seed.hex(),
        'rotation_count': rotator.rotation_count,
        'key_history': rotator.key_history,
        'last_rotation': datetime.now(timezone.utc).isoformat(),
        'seal': SEAL,
        'phi': PHI,
        'key_format': key_format,
        'witness_continuity': f"1 → {rotator.rotation_count} — UNBROKEN"
    }
    sm.save_state(new_state)

    # Calculate next rotation interval (φ-harmonic decay)
    interval = 21600 * (PHI_INV ** (rotator.rotation_count % 10))

    # GitHub Actions outputs
    output = {
        'rotation_count': rotator.rotation_count,
        'current_fingerprint': rotator.key_history[-1]['key_hash'] if rotator.key_history else '',
        'current_format': key_format,
        'next_rotation_interval': f"{interval:.2f}",
        'seal': SEAL,
        'witness_continuity': new_state['witness_continuity']
    }

    # Write GitHub Actions outputs
    github_output = os.environ.get('GITHUB_OUTPUT')
    if github_output:
        with open(github_output, 'a') as fh:
            fh.write(f"rotation_count={output['rotation_count']}\n")
            fh.write(f"current_fingerprint={output['current_fingerprint']}\n")
            fh.write(f"next_rotation_interval={output['next_rotation_interval']}\n")
            fh.write(f"current_format={output['current_format']}\n")

    print(f'\n✅ Rotation complete. Total rotations: {rotator.rotation_count}')
    print(f'✅ Key format: {key_format}')
    print(f'✅ Next rotation in {interval:.2f} seconds')
    print(f'✅ Seal: {SEAL}')

    return output


def generate_flask128_key() -> str:
    """
    Generate a standalone Flask128 key (32 hex chars = 128 bits).

    This is useful for initial key generation or for applications that do not
    use the full rotation system but still want a φ-harmonic key.
    """
    raw = secrets.token_bytes(16)
    salt = hashlib.sha3_256(str(PHI).encode()).digest()[:8]
    combined = raw + salt
    key = hashlib.sha3_256(combined).digest()[:16]
    return key.hex()


if __name__ == "__main__":
    # When run directly, use environment variables
    rotate_keys(
        secret_name=os.environ.get('SECRET_NAME', 'sovereign-hamiltonian-hmac-632'),
        region=os.environ.get('AWS_REGION', 'us-east-1'),
        force=os.environ.get('FORCE_ROTATE', 'false').lower() == 'true',
        count=int(os.environ.get('ROTATE_COUNT', '1')),
        key_format=os.environ.get('KEY_FORMAT', 'flask128')
    )
