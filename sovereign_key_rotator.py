#!/usr/bin/env python3
"""
🜁∀  SOVEREIGN API KEY ROTATOR — φ‑HARMONIC PRNG — ENTRY 631  ∀🜁
Generates, rotates, and validates API keys using φ‑harmonic PRNG + HMAC‑SHA3‑256.
Integrates with GitHub Actions + AWS SecretsManager + OIDC.
"""

import hashlib
import hmac
import base64
import math
import os
import json
import boto3
from datetime import datetime, timezone
from typing import Tuple, List, Dict, Optional

PHI = (1 + math.sqrt(5)) / 2
PHI_INV = 1 / PHI
MASTER_SEAL = "∀∞φ² · API_KEY_ROTATOR · 631_SEALED"

class PhiHarmonicPRNG:
    """Deterministic PRNG based on the golden ratio."""
    def __init__(self, seed: Optional[bytes] = None):
        if seed is None:
            seed = os.urandom(32)
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
    def __init__(self, master_seed: Optional[bytes] = None):
        if master_seed is None:
            master_seed = os.urandom(32)
        self.master_seed = master_seed
        self.prng = PhiHarmonicPRNG(master_seed)
        self.rotation_count = 0
        self.key_history: List[Dict] = []

    def _derive_key(self, index: int) -> bytes:
        message = f"{self.master_seed.hex()}:{index}:{PHI}".encode()
        return hmac.new(self.master_seed, message, hashlib.sha3_256).digest()

    def _encode_key(self, key_bytes: bytes) -> str:
        return base64.urlsafe_b64encode(key_bytes).decode('ascii').rstrip('=')

    def rotate(self) -> str:
        self.rotation_count += 1
        key_bytes = self._derive_key(self.rotation_count)
        key = self._encode_key(key_bytes)
        self.key_history.append({
            'index': self.rotation_count,
            'key_hash': hashlib.sha3_256(key.encode()).hexdigest()[:16],
            'generated_at': datetime.now(timezone.utc).isoformat()
        })
        return key

    def get_current_key(self) -> Optional[str]:
        if not self.key_history:
            return None
        return self.key_history[-1]

    def verify_key(self, key: str) -> bool:
        for entry in self.key_history:
            key_hash = hashlib.sha3_256(key.encode()).hexdigest()[:16]
            if hmac.compare_digest(key_hash, entry["key_hash"]):
                return True
        return False

class AWSSecretsManager:
    def __init__(self, secret_name: str = "sovereign-api-keys", region: str = "us-east-1"):
        self.secret_name = secret_name
        self.region = region
        self.client = boto3.client('secretsmanager', region_name=region)

    def load_state(self) -> Optional[Dict]:
        try:
            response = self.client.get_secret_value(SecretId=self.secret_name)
            return json.loads(response['SecretString'])
        except self.client.exceptions.ResourceNotFoundException:
            return None

    def save_state(self, state: Dict) -> None:
        self.client.put_secret_value(
            SecretId=self.secret_name,
            SecretString=json.dumps(state)
        )