# ci_cd_key_rotator.py
# Entry 711 — Sovereign Hamiltonian Key Rotator

import json
import hashlib
import os
import time
from typing import Dict, Any, Optional
from dataclasses import dataclass

PHI = (1 + 5 ** 0.5) / 2

@dataclass
class CI_CD_KeyRotator:
    rotation_count: int = 0
    current_key: Optional[str] = None
    previous_key: Optional[str] = None
    last_rotation: Optional[str] = None
    witness_continuity: str = "1 → 711 — UNBROKEN"
    seal: str = "∀∞φ² · KEY_ROTATION · 711_SEALED"
    state_file: str = "rotation_state_711.json"

    def load_state(self) -> bool:
        try:
            with open(self.state_file, 'r') as f:
                data = json.load(f)
            self.rotation_count = data.get('rotation_count', 0)
            self.current_key = data.get('current_key')
            self.previous_key = data.get('previous_key')
            self.last_rotation = data.get('last_rotation')
            self.witness_continuity = data.get('witness_continuity', "1 → 711 — UNBROKEN")
            self.seal = data.get('seal', "∀∞φ² · KEY_ROTATION · 711_SEALED")
            return True
        except FileNotFoundError:
            return False

    def save_state(self) -> None:
        data = {
            'rotation_count': self.rotation_count,
            'current_key': self.current_key,
            'previous_key': self.previous_key,
            'last_rotation': self.last_rotation,
            'witness_continuity': self.witness_continuity,
            'seal': self.seal
        }
        with open(self.state_file, 'w') as f:
            json.dump(data, f, indent=2)

    def generate_key(self, entropy: str = None) -> str:
        if entropy is None:
            entropy = str(time.time_ns())
        seed = f"{entropy}:{self.rotation_count}:{PHI}".encode()
        return hashlib.sha3_256(seed).hexdigest()

    def rotate(self, force: bool = False) -> Dict[str, Any]:
        if not force and self.rotation_count > 0:
            if self.last_rotation:
                from datetime import datetime, timezone
                last = datetime.fromisoformat(self.last_rotation)
                now = datetime.now(timezone.utc)
                if (now - last).total_seconds() < 21600:
                    return {
                        'status': 'SKIPPED',
                        'reason': 'Next rotation scheduled in φ-harmonic interval',
                        'rotation_count': self.rotation_count
                    }
        self.previous_key = self.current_key
        self.current_key = self.generate_key()
        self.rotation_count += 1
        from datetime import datetime, timezone
        self.last_rotation = datetime.now(timezone.utc).isoformat()
        self.witness_continuity = f"1 → {self.rotation_count} — UNBROKEN"
        self.seal = f"∀∞φ² · KEY_ROTATION · {self.rotation_count}_SEALED"
        self.save_state()
        return {
            'status': 'ROTATED',
            'rotation_count': self.rotation_count,
            'current_key_fingerprint': hashlib.sha3_256(self.current_key.encode()).hexdigest()[:16],
            'last_rotation': self.last_rotation,
            'seal': self.seal,
            'witness_continuity': self.witness_continuity
        }
