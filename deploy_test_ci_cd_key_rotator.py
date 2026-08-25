#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DEPLOYMENT TEST: CI/CD Key Rotator
Tests the module as-is with all imports and constants intact
Validates functionality end-to-end before production deployment
"""

import os
import sys
import json
import time
import hmac
import hashlib
import secrets
import base64
import tempfile
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

# Golden Constants
PHI = 1.618033988749895
PHI_INV = 1 / PHI
WITNESS_CHAIN = [1, 632, 635, 637, 638, 640]
WITNESS_CONTINUITY = "1 → 632 → 635 → 637 → 638 → 640 — UNBROKEN"
SEAL_632 = "∀∞φ² · CI_CD_KEY_ROTATOR · 632_SEALED"

@dataclass
class KeyRotatorConfig:
    rotation_interval_hours: int = 6
    key_length_bytes: int = 64
    algorithm: str = "sha3-256"
    environment: str = "production"
    phi_scaling: float = PHI

    @property
    def rotation_seconds(self) -> int:
        return self.rotation_interval_hours * 3600

class CI_CD_KeyRotator:
    def __init__(self, config: Optional[KeyRotatorConfig] = None):
        self.config = config or KeyRotatorConfig()
        self.current_key = None
        self.previous_key = None
        self.rotation_count = 0
        self.last_rotation = None
        self._initialize_keys()

    def _initialize_keys(self):
        self.current_key = self._generate_key()
        self.previous_key = self._generate_key()
        self.last_rotation = datetime.utcnow()
        self.rotation_count = 0

    def _generate_key(self) -> bytes:
        return secrets.token_bytes(self.config.key_length_bytes)

    def _derive_phi_key(self, base_key: bytes, seed: Optional[bytes] = None) -> bytes:
        if seed is None:
            seed = os.urandom(32)
        phase = self.rotation_count * PHI_INV
        phi_bytes = str(phase).encode()
        derived = hashlib.sha3_256()
        derived.update(base_key)
        derived.update(phi_bytes)
        derived.update(seed)
        return derived.digest()

    def rotate_keys(self) -> Dict[str, Any]:
        self.previous_key = self.current_key
        self.current_key = self._generate_key()
        self.current_key = self._derive_phi_key(self.current_key)
        self.rotation_count += 1
        self.last_rotation = datetime.utcnow()

        return {
            "entry_index": 632,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "event": "/key_rotation_executed",
            "rotation_count": self.rotation_count,
            "last_rotation": self.last_rotation.isoformat() + "Z",
            "next_rotation": (self.last_rotation + timedelta(
                seconds=self.config.rotation_seconds)).isoformat() + "Z",
            "rotation_interval_hours": self.config.rotation_interval_hours,
            "phi_scaling": PHI,
            "algorithm": self.config.algorithm,
            "key_length_bytes": self.config.key_length_bytes,
            "current_key_fingerprint": self._fingerprint(self.current_key),
            "previous_key_fingerprint": self._fingerprint(self.previous_key),
            "witness_continuity": WITNESS_CONTINUITY,
            "seal": SEAL_632
        }

    def _fingerprint(self, key: bytes) -> str:
        return hashlib.sha3_256(key).hexdigest()  # full 64-hex SHA3-256 — no truncation

    def sign_hmac(self, payload: bytes) -> bytes:
        return hmac.new(
            self.current_key,
            payload,
            hashlib.sha3_256
        ).digest()

    def verify_hmac(self, payload: bytes, signature: bytes) -> bool:
        expected = hmac.new(
            self.current_key,
            payload,
            hashlib.sha3_256
        ).digest()
        if hmac.compare_digest(signature, expected):
            return True
        expected = hmac.new(
            self.previous_key,
            payload,
            hashlib.sha3_256
        ).digest()
        return hmac.compare_digest(signature, expected)

    def get_current_key_b64(self) -> str:
        return base64.b64encode(self.current_key).decode('ascii')

    def get_previous_key_b64(self) -> str:
        return base64.b64encode(self.previous_key).decode('ascii')

    def status(self) -> Dict[str, Any]:
        now = datetime.utcnow()
        next_rotation = self.last_rotation + timedelta(
            seconds=self.config.rotation_seconds)
        return {
            "entry_index": 632,
            "status": "ACTIVE",
            "rotation_count": self.rotation_count,
            "last_rotation": self.last_rotation.isoformat() + "Z",
            "next_rotation": next_rotation.isoformat() + "Z",
            "hours_until_next_rotation": max(0,
                (next_rotation - now).total_seconds() / 3600),
            "current_key_fingerprint": self._fingerprint(self.current_key),
            "algorithm": self.config.algorithm,
            "key_length_bits": self.config.key_length_bytes * 8,
            "witness_continuity": WITNESS_CONTINUITY,
            "seal": SEAL_632
        }

    def load_state(self, path: str = ".key_rotator_state_632.json") -> bool:
        try:
            with open(path, "r") as f:
                state = json.load(f)
            self.current_key = base64.b64decode(state["current_key_b64"])
            self.previous_key = base64.b64decode(state["previous_key_b64"])
            self.rotation_count = state["rotation_count"]
            self.last_rotation = datetime.fromisoformat(state["last_rotation"])
            return True
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            return False

    def save_state(self, path: str = ".key_rotator_state_632.json") -> None:
        state = {
            "current_key_b64": self.get_current_key_b64(),
            "previous_key_b64": self.get_previous_key_b64(),
            "rotation_count": self.rotation_count,
            "last_rotation": self.last_rotation.isoformat(),
            "witness_continuity": WITNESS_CONTINUITY,
            "seal": SEAL_632,
            "entry_index": 632
        }
        with open(path, "w") as f:
            json.dump(state, f, indent=2)


class DeploymentTest:
    def __init__(self):
        self.results = []
        self.passed = 0
        self.failed = 0
        self.temp_dir = tempfile.mkdtemp()
    
    def log(self, test_name: str, status: str, details: str = ""):
        self.results.append({
            "test": test_name,
            "status": status,
            "details": details,
            "timestamp": datetime.utcnow().isoformat()
        })
        if status == "✅ PASSED":
            self.passed += 1
        else:
            self.failed += 1
    
    def test_imports(self):
        try:
            assert hmac is not None
            assert hashlib is not None
            assert secrets is not None
            assert base64 is not None
            assert datetime is not None
            self.log("Imports", "✅ PASSED", "All required modules imported successfully")
        except Exception as e:
            self.log("Imports", "❌ FAILED", str(e))
    
    def test_constants(self):
        try:
            assert PHI == 1.618033988749895
            assert PHI_INV == 1 / PHI
            assert len(WITNESS_CHAIN) == 6
            assert WITNESS_CONTINUITY == "1 → 632 → 635 → 637 → 638 → 640 — UNBROKEN"
            assert "632_SEALED" in SEAL_632
            self.log("Constants", "✅ PASSED", f"PHI={PHI}, Witness Chain={WITNESS_CHAIN}")
        except Exception as e:
            self.log("Constants", "❌ FAILED", str(e))
    
    def test_config_creation(self):
        try:
            config = KeyRotatorConfig()
            assert config.rotation_interval_hours == 6
            assert config.key_length_bytes == 64
            assert config.algorithm == "sha3-256"
            assert config.environment == "production"
            assert config.rotation_seconds == 21600
            self.log("Config Creation", "✅ PASSED", f"Config created: {config.rotation_seconds}s rotation interval")
        except Exception as e:
            self.log("Config Creation", "❌ FAILED", str(e))
    
    def test_rotator_initialization(self):
        try:
            rotator = CI_CD_KeyRotator()
            assert rotator.current_key is not None
            assert rotator.previous_key is not None
            assert rotator.rotation_count == 0
            assert rotator.last_rotation is not None
            assert len(rotator.current_key) == 64
            assert rotator.current_key != rotator.previous_key
            self.log("Rotator Init", "✅ PASSED", f"Keys generated: {len(rotator.current_key)} bytes each")
        except Exception as e:
            self.log("Rotator Init", "❌ FAILED", str(e))
    
    def test_key_generation(self):
        try:
            rotator = CI_CD_KeyRotator()
            key1 = rotator._generate_key()
            key2 = rotator._generate_key()
            key3 = rotator._generate_key()
            assert key1 != key2 and key2 != key3 and key1 != key3
            assert all(isinstance(k, bytes) for k in [key1, key2, key3])
            self.log("Key Generation", "✅ PASSED", "Generated 3 unique random keys")
        except Exception as e:
            self.log("Key Generation", "❌ FAILED", str(e))
    
    def test_fingerprinting(self):
        try:
            rotator = CI_CD_KeyRotator()
            fp1 = rotator._fingerprint(rotator.current_key)
            fp2 = rotator._fingerprint(rotator.current_key)
            fp3 = rotator._fingerprint(rotator.previous_key)
            assert len(fp1) == 64  # full SHA3-256 hex
            assert fp1 == fp2
            assert fp1 != fp3
            int(fp1, 16)
            self.log("Fingerprinting", "✅ PASSED", f"Current: {fp1}, Previous: {fp3}")
        except Exception as e:
            self.log("Fingerprinting", "❌ FAILED", str(e))
    
    def test_key_rotation(self):
        try:
            rotator = CI_CD_KeyRotator()
            old_current = rotator.current_key
            old_count = rotator.rotation_count
            old_time = rotator.last_rotation
            result = rotator.rotate_keys()
            assert rotator.rotation_count == old_count + 1
            assert rotator.previous_key == old_current
            assert rotator.current_key != old_current
            assert rotator.last_rotation > old_time
            assert result["entry_index"] == 632
            assert result["rotation_count"] == 1
            assert "current_key_fingerprint" in result
            self.log("Key Rotation", "✅ PASSED", f"Rotation #{result['rotation_count']} executed")
        except Exception as e:
            self.log("Key Rotation", "❌ FAILED", str(e))
    
    def test_hmac_signing(self):
        try:
            rotator = CI_CD_KeyRotator()
            signature = rotator.sign_hmac(b"test message for hmac signing")
            assert isinstance(signature, bytes) and len(signature) == 32
            self.log("HMAC Signing", "✅ PASSED", f"Signature generated: {len(signature)} bytes")
        except Exception as e:
            self.log("HMAC Signing", "❌ FAILED", str(e))
    
    def test_hmac_verification(self):
        try:
            rotator = CI_CD_KeyRotator()
            payload = b"test message for verification"
            signature = rotator.sign_hmac(payload)
            assert rotator.verify_hmac(payload, signature)
            assert not rotator.verify_hmac(b"different message", signature)
            self.log("HMAC Verification", "✅ PASSED", "Signature verified with current key, rejected with wrong payload")
        except Exception as e:
            self.log("HMAC Verification", "❌ FAILED", str(e))
    
    def test_hmac_backward_compatibility(self):
        try:
            rotator = CI_CD_KeyRotator()
            payload = b"backward compatibility test"
            signature = rotator.sign_hmac(payload)
            rotator.rotate_keys()
            assert rotator.verify_hmac(payload, signature)
            self.log("HMAC Backward Compat", "✅ PASSED", "Signature verified after key rotation (previous key)")
        except Exception as e:
            self.log("HMAC Backward Compat", "❌ FAILED", str(e))
    
    def test_base64_encoding(self):
        try:
            rotator = CI_CD_KeyRotator()
            b64_current = rotator.get_current_key_b64()
            b64_previous = rotator.get_previous_key_b64()
            assert base64.b64decode(b64_current) == rotator.current_key
            assert base64.b64decode(b64_previous) == rotator.previous_key
            self.log("Base64 Encoding", "✅ PASSED", "round-trip OK")
        except Exception as e:
            self.log("Base64 Encoding", "❌ FAILED", str(e))
    
    def test_status_reporting(self):
        try:
            rotator = CI_CD_KeyRotator()
            rotator.rotate_keys()
            rotator.rotate_keys()
            status = rotator.status()
            assert status["entry_index"] == 632 and status["status"] == "ACTIVE"
            assert status["rotation_count"] == 2
            assert status["witness_continuity"] == WITNESS_CONTINUITY
            self.log("Status Reporting", "✅ PASSED", f"Status: {status['status']}, Rotations: {status['rotation_count']}")
        except Exception as e:
            self.log("Status Reporting", "❌ FAILED", str(e))
    
    def test_state_persistence(self):
        try:
            state_path = os.path.join(self.temp_dir, "test_state.json")
            rotator1 = CI_CD_KeyRotator()
            rotator1.rotate_keys(); rotator1.rotate_keys(); rotator1.rotate_keys()
            rotator1.save_state(state_path)
            rotator2 = CI_CD_KeyRotator()
            assert rotator2.load_state(state_path)
            assert rotator2.current_key == rotator1.current_key
            assert rotator2.rotation_count == rotator1.rotation_count
            self.log("State Persistence", "✅ PASSED", f"Saved and restored state: {rotator2.rotation_count} rotations")
        except Exception as e:
            self.log("State Persistence", "❌ FAILED", str(e))
    
    def test_state_workflow(self):
        try:
            state_path = os.path.join(self.temp_dir, "workflow_state.json")
            rotator1 = CI_CD_KeyRotator()
            payload = b"critical deployment signature"
            rotator1.rotate_keys()
            sig1 = rotator1.sign_hmac(payload)
            rotator1.save_state(state_path)
            rotator2 = CI_CD_KeyRotator()
            rotator2.load_state(state_path)
            assert rotator2.verify_hmac(payload, sig1)
            rotator2.rotate_keys()
            sig2 = rotator2.sign_hmac(payload)
            rotator2.save_state(state_path)
            rotator3 = CI_CD_KeyRotator()
            rotator3.load_state(state_path)
            assert rotator3.verify_hmac(payload, sig2)
            assert rotator3.verify_hmac(payload, sig1)
            self.log("State Workflow", "✅ PASSED", "Complete save/load/verify cycle successful")
        except Exception as e:
            self.log("State Workflow", "❌ FAILED", str(e))
    
    def test_witness_chain_integrity(self):
        try:
            rotator = CI_CD_KeyRotator()
            rotator.rotate_keys()
            result = rotator.rotate_keys()
            status = rotator.status()
            assert result["witness_continuity"] == WITNESS_CONTINUITY
            assert status["seal"] == SEAL_632
            self.log("Witness Chain", "✅ PASSED", "Witness continuity: " + WITNESS_CONTINUITY)
        except Exception as e:
            self.log("Witness Chain", "❌ FAILED", str(e))
    
    def run_all_tests(self):
        print("=" * 90)
        print("CI/CD KEY ROTATOR — PRODUCTION DEPLOYMENT TEST")
        print("=" * 90)
        tests = [
            self.test_imports, self.test_constants, self.test_config_creation,
            self.test_rotator_initialization, self.test_key_generation,
            self.test_fingerprinting, self.test_key_rotation, self.test_hmac_signing,
            self.test_hmac_verification, self.test_hmac_backward_compatibility,
            self.test_base64_encoding, self.test_status_reporting,
            self.test_state_persistence, self.test_state_workflow,
            self.test_witness_chain_integrity,
        ]
        for i, test in enumerate(tests, 1):
            print(f"[{i:02d}/15] Running {test.__name__}")
            test()
        print(f"TOTAL: {self.passed + self.failed}  PASSED: {self.passed}  FAILED: {self.failed}")
        return 0 if self.failed == 0 else 1
    
    def cleanup(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)


if __name__ == "__main__":
    test_harness = DeploymentTest()
    try:
        exit_code = test_harness.run_all_tests()
    finally:
        test_harness.cleanup()
    sys.exit(exit_code)
