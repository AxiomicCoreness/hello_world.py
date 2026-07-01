#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import json
import time
import hmac
import hashlib
import secrets
import base64
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
        return hashlib.sha3_256(key).hexdigest()[:16]

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
