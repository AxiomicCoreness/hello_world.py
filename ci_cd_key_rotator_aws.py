"""Declared-shape rotator stub (AWS half).

Replaces the prior version of this file, which imported boto3 and
sovereign_key_rotator.SovereignKeyRotator - an import chain that fails
in CI whenever either dependency is absent, and which made real AWS
calls this pipeline never authorized.

Contract: the workflow reads these exact keys from rotate_keys() and
status() outputs:
  rotation_count, current_key_fingerprint, witness_continuity,
  seal, next_rotation
The keys are the contract. The values below are explicit non-claims:
no key material, no witness continuity, no seal. A stub that emitted a
"..._SEALED" string or an "UNBROKEN" claim would be a ghost seal, and
would additionally make this file unverifiable by
.github/scripts/verify_ledger_seals.py.

Real AWS calls: not implemented - declared shape only.
This module can fail: missing or corrupt state file -> load_state() False.
"""
import json
from pathlib import Path

STATE_PATH = Path("ci_cd_key_rotator_aws_state.json")


def _stub_payload(rotation_count: int) -> dict:
    return {
        "rotation_count": rotation_count,
        "current_key_fingerprint": "stub: no key material",
        "witness_continuity": "stub: no witness claim",
        "seal": "stub: unsealed",
        "next_rotation": "stub: no schedule",
    }


class AWSSecretsManagerRotator:
    def __init__(self, secret_name: str, region: str = "us-east-1") -> None:
        self.secret_name = secret_name
        self.region = region
        self.rotation_count = 0

    def load_state(self) -> bool:
        if not STATE_PATH.is_file():
            return False
        try:
            data = json.loads(STATE_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return False
        count = (
            data.get("rotation_count", 0) if isinstance(data, dict) else None
        )
        if not isinstance(count, int) or count < 0:
            return False
        self.rotation_count = count
        return True

    def rotate_keys(self) -> dict:
        self.rotation_count += 1
        return _stub_payload(self.rotation_count)

    def status(self) -> dict:
        return _stub_payload(self.rotation_count)
