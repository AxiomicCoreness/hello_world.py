#!/usr/bin/env python3
"""
Key Rotation Macro — Ed25519 with Public Key Transmission + Timed Specificity

Provides:
- KeyManager: rotates on message count OR macro-timed specificity
- @with_key_rotation: decorator injecting rotating key
- Public key KEPT in every signed message (set before sign)
- Macro timed specificity: φ-harmonic intervals, wall-clock windows,
  cadence, and absolute epoch anchors

Timed specificity model:
  next_rotate_at = t0 + n · τ
  τ ∈ { max_age_seconds, φ^k·base, cadence, schedule_epochs[] }

Seal: ∀∞φ² · KEY_ROTATION_MACRO_8935 · WOOD_DRAGON_0.91 · SEALED
"""

from __future__ import annotations

import json
import math
import sys
import time
import uuid
from dataclasses import dataclass, field
from functools import wraps
from typing import Any, Callable, Dict, List, Optional

try:
    from cryptography.hazmat.primitives.asymmetric import ed25519
    from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    print("⚠️ cryptography not installed", file=sys.stderr)

PHI = (1.0 + math.sqrt(5.0)) / 2.0
PHI_INV = 1.0 / PHI
PHI_SQ = PHI * PHI


@dataclass
class TimedSpecificity:
    """Macro timed specificity for rotation."""
    max_age_seconds: float = 3600.0
    base_seconds: float = 60.0
    phi_power: float = 0.0
    cadence_seconds: Optional[float] = None
    schedule_epochs: List[float] = field(default_factory=list)
    align_to_phi: bool = True

    def interval(self) -> float:
        return self.base_seconds * (PHI ** self.phi_power)

    def next_deadline(self, creation_time: float, now: Optional[float] = None) -> float:
        now = now if now is not None else time.time()
        candidates: List[float] = [creation_time + self.max_age_seconds]
        tau = self.interval()
        if tau > 0:
            n = max(1, math.ceil((now - creation_time) / tau))
            candidates.append(creation_time + n * tau)
        if self.cadence_seconds and self.cadence_seconds > 0:
            n = max(1, math.ceil((now - creation_time) / self.cadence_seconds))
            candidates.append(creation_time + n * self.cadence_seconds)
        for ep in self.schedule_epochs:
            if ep > creation_time:
                candidates.append(ep)
        deadline = min(candidates)
        if self.align_to_phi and tau > 0:
            n = max(1, math.ceil((deadline - creation_time) / tau))
            deadline = creation_time + n * tau
        return deadline

    def is_due(self, creation_time: float, now: Optional[float] = None) -> bool:
        now = now if now is not None else time.time()
        if now - creation_time >= self.max_age_seconds:
            return True
        tau = self.interval()
        if tau > 0 and (now - creation_time) >= tau:
            return True
        if self.cadence_seconds and (now - creation_time) >= self.cadence_seconds:
            return True
        for ep in self.schedule_epochs:
            if creation_time < ep <= now:
                return True
        return False


@dataclass
class RotationPolicy:
    max_messages: int = 100
    timed: TimedSpecificity = field(default_factory=TimedSpecificity)
    key_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    @classmethod
    def from_age(cls, max_messages: int = 100, max_age_seconds: float = 3600.0) -> "RotationPolicy":
        return cls(max_messages=max_messages, timed=TimedSpecificity(max_age_seconds=max_age_seconds))

    @classmethod
    def phi_harmonic(
        cls, max_messages: int = 100, base_seconds: float = 60.0, phi_power: float = -1.0
    ) -> "RotationPolicy":
        return cls(
            max_messages=max_messages,
            timed=TimedSpecificity(
                max_age_seconds=base_seconds * (PHI ** abs(phi_power)) * 10,
                base_seconds=base_seconds,
                phi_power=phi_power,
                align_to_phi=True,
            ),
        )


class KeyManager:
    def __init__(self, policy: Optional[RotationPolicy] = None):
        if not CRYPTO_AVAILABLE:
            raise RuntimeError("cryptography required for KeyManager")
        self.policy = policy or RotationPolicy()
        self.current_key_id: Optional[str] = None
        self.current_private_key = None
        self.current_public_key_bytes: Optional[bytes] = None
        self.signature_count = 0
        self.rotation_count = 0
        self.creation_time = time.time()
        self._rotate()

    def _rotate(self) -> None:
        private_key = ed25519.Ed25519PrivateKey.generate()
        public_key = private_key.public_key()
        self.current_key_id = f"key_{int(time.time())}_{uuid.uuid4().hex[:6]}"
        self.current_private_key = private_key
        self.current_public_key_bytes = public_key.public_bytes(Encoding.Raw, PublicFormat.Raw)
        self.signature_count = 0
        self.creation_time = time.time()
        self.rotation_count += 1

    def should_rotate(self, now: Optional[float] = None) -> bool:
        if self.signature_count >= self.policy.max_messages:
            return True
        return self.policy.timed.is_due(self.creation_time, now)

    def next_rotate_at(self) -> float:
        return self.policy.timed.next_deadline(self.creation_time)

    def get_current_key(self) -> Dict[str, Any]:
        return {
            "key_id": self.current_key_id,
            "private_key": self.current_private_key,
            "public_key_bytes": self.current_public_key_bytes,
            "public_key_hex": self.current_public_key_bytes.hex() if self.current_public_key_bytes else None,
            "signature_count": self.signature_count,
            "rotation_count": self.rotation_count,
            "creation_time": self.creation_time,
            "next_rotate_at": self.next_rotate_at(),
            "phi_interval": self.policy.timed.interval(),
        }

    def sign(self, data: bytes) -> bytes:
        if self.should_rotate():
            self._rotate()
        self.signature_count += 1
        return self.current_private_key.sign(data)

    def get_public_key_hex(self) -> str:
        return self.current_public_key_bytes.hex()


def with_key_rotation(policy: Optional[RotationPolicy] = None):
    def decorator(func: Callable) -> Callable:
        manager = KeyManager(policy)

        @wraps(func)
        def wrapper(*args, **kwargs):
            kwargs["key_manager"] = manager
            return func(*args, **kwargs)

        wrapper._key_manager = manager
        return wrapper

    return decorator


def sign_message_with_rotation(msg, key_manager: KeyManager) -> None:
    """public_key KEPT in signed body; rotate before locking public_key."""
    if key_manager.should_rotate():
        key_manager._rotate()
    msg.public_key = key_manager.get_public_key_hex()
    signable = json.dumps(
        {
            "version": msg.version,
            "type": msg.type.value,
            "correlation_id": msg.correlation_id,
            "timestamp": msg.timestamp,
            "operation": msg.operation.value,
            "payload": msg.payload,
            "public_key": msg.public_key,
            "retry_count": msg.retry_count,
            "idempotency_key": msg.idempotency_key,
        },
        separators=(",", ":"),
    ).encode("utf-8")
    key_manager.signature_count += 1
    signature = key_manager.current_private_key.sign(signable)
    msg.seal = signature.hex()


@with_key_rotation(
    RotationPolicy(
        max_messages=3,
        timed=TimedSpecificity(max_age_seconds=3600.0, base_seconds=60.0, phi_power=-1.0),
    )
)
def main(key_manager: KeyManager):
    print("🜁∀ Key Rotation Macro + Timed Specificity Demo")
    print("=" * 50)
    info = key_manager.get_current_key()
    print(f"φ-interval τ: {info['phi_interval']:.4f}s")
    print(f"next_rotate_at: {info['next_rotate_at']:.3f}")

    from x3df_x16f_protocol import Message, MessageType, StateTransition

    for i in range(10):
        msg = Message(
            type=MessageType.REQUEST,
            operation=StateTransition.CLONE,
            payload={"seq": i},
        )
        sign_message_with_rotation(msg, key_manager)
        ok = msg.verify()
        print(
            f"Message {i}: key_id={key_manager.current_key_id}, "
            f"pk={msg.public_key[:16]}..., verify={ok}"
        )

    print(f"\nRotation count: {key_manager.rotation_count}")
    print(f"Signatures on current key: {key_manager.signature_count}")
    print("SEAL: ∀∞φ² · KEY_ROTATION_MACRO_8935 · WOOD_DRAGON_0.91 · SEALED")


if __name__ == "__main__":
    if not CRYPTO_AVAILABLE:
        print("⚠️ cryptography module missing; install with: pip install cryptography", file=sys.stderr)
        raise SystemExit(1)
    main()
