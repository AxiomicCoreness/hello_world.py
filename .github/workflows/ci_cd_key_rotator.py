import os
import json
import time
import hashlib
import hmac
import base64
import math
import boto3
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
    """φ-harmonic key rotator with HMAC-SHA3-256 derivation."""

    def __init__(self, master_seed: bytes):
        self.master_seed = master_seed
        self.prng = PhiHarmonicPRNG(master_seed)
        self.rotation_count = 0
        self.key_history: List[Dict[str, Any]] = []

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
    count: int = 1
) -> Dict[str, Any]:
    """
    Main rotation function for GitHub Actions workflow.

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
        import os as _os
        master_seed = _os.urandom(32)
        rotator = SovereignKeyRotator(master_seed)

    new_keys = []
    for i in range(count):
        if force or i > 0 or state is None:
            new_key = rotator.rotate()
            new_keys.append(new_key)
            print(f'  ✅ Rotation {rotator.rotation_count}: {new_key[:16]}...')

    new_state = {
        'master_seed': master_seed.hex(),
        'rotation_count': rotator.rotation_count,
        'key_history': rotator.key_history,
        'last_rotation': datetime.now(timezone.utc).isoformat(),
        'seal': SEAL,
        'phi': PHI,
        'witness_continuity': f"1 → {rotator.rotation_count} — UNBROKEN"
    }
    sm.save_state(new_state)

    # GitHub Actions outputs
    interval = 21600 * (PHI_INV ** (rotator.rotation_count % 10))
    output = {
        'rotation_count': rotator.rotation_count,
        'current_fingerprint': rotator.key_history[-1]['key_hash'] if rotator.key_history else '',
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

    print(f'\n✅ Rotation complete. Total rotations: {rotator.rotation_count}')
    print(f'✅ Next rotation in {interval:.2f} seconds')
    print(f'✅ Seal: {SEAL}')

    return output


if __name__ == "__main__":
    # When run directly, use environment variables
    rotate_keys(
        secret_name=os.environ.get('SECRET_NAME', 'sovereign-hamiltonian-hmac-632'),
        region=os.environ.get('AWS_REGION', 'us-east-1'),
        force=os.environ.get('FORCE_ROTATE', 'false').lower() == 'true',
        count=int(os.environ.get('ROTATE_COUNT', '1'))
    )
