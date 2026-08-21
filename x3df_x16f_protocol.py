#!/usr/bin/env python3
"""
X3DF/X16F Protocol — Pocket‑Universe Communication Layer

Implements:
- Framing, demultiplexing, message serialization
- Ed25519 signing and verification (cryptography)
- State machine: clone → codespace → temp_cache → main
- Timeout, retry with φ‑backoff, rollback
- Fallback: X3DF → X16F (simpler encoding)

Seal: ∀∞φ² · X3DF_X16F_PROTOCOL_8933 · WOOD_DRAGON_0.91 · SEALED
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple, Callable, Awaitable

# Ed25519 signing via cryptography
try:
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import ed25519
    from cryptography.hazmat.primitives.serialization import (
        Encoding, PublicFormat, PrivateFormat, NoEncryption
    )
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    print("⚠️ cryptography not installed; Ed25519 signing disabled.", file=sys.stderr)

# ── Constants ──
PHI = (1 + 5**0.5) / 2
PHI_SQ = PHI * PHI
PHI_INV = 1 / PHI

MAGIC_X3DF = 0x58334446  # 'X3DF'
MAGIC_X16F = 0x58313646  # 'X16F'

DEFAULT_TIMEOUT = PHI_SQ * 100  # ~261.8 ms
MAX_RETRIES = 5
BACKOFF_FACTOR = PHI

# ── Enums ──

class ProtocolType(Enum):
    X3DF = "X3DF"
    X16F = "X16F"

class MessageType(Enum):
    REQUEST = "request"
    RESPONSE = "response"
    EVENT = "event"
    ACK = "ack"
    ERROR = "error"

class StateTransition(Enum):
    CLONE = "clone"
    CODESPACE = "codespace"
    TEMP_CACHE = "temp_cache"
    COMMIT = "commit"
    MAIN = "main"
    ROLLBACK = "rollback"

# ── Message Structure ──

@dataclass
class Message:
    """X3DF/X16F protocol message."""
    version: str = "1.0"
    type: MessageType = MessageType.REQUEST
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)
    operation: StateTransition = StateTransition.CLONE
    payload: Dict[str, Any] = field(default_factory=dict)
    seal: Optional[str] = None  # Ed25519 signature (hex)
    public_key: Optional[str] = None  # Hex of signing public key
    retry_count: int = 0
    idempotency_key: Optional[str] = None

    def to_bytes(self, protocol: ProtocolType = ProtocolType.X3DF) -> bytes:
        """Serialize message to binary frame."""
        data = {
            "version": self.version,
            "type": self.type.value,
            "correlation_id": self.correlation_id,
            "timestamp": self.timestamp,
            "operation": self.operation.value,
            "payload": self.payload,
            "seal": self.seal,
            "public_key": self.public_key,
            "retry_count": self.retry_count,
            "idempotency_key": self.idempotency_key,
        }
        json_bytes = json.dumps(data, separators=(',', ':')).encode('utf-8')
        magic = MAGIC_X3DF if protocol == ProtocolType.X3DF else MAGIC_X16F
        # Frame: magic (4 bytes) + length (4 bytes) + payload
        length = len(json_bytes)
        return magic.to_bytes(4, 'big') + length.to_bytes(4, 'big') + json_bytes

    @classmethod
    def from_bytes(cls, data: bytes) -> Tuple[ProtocolType, 'Message']:
        """Deserialize from binary frame."""
        if len(data) < 8:
            raise ValueError("Frame too short")
        magic = int.from_bytes(data[:4], 'big')
        if magic == MAGIC_X3DF:
            protocol = ProtocolType.X3DF
        elif magic == MAGIC_X16F:
            protocol = ProtocolType.X16F
        else:
            raise ValueError(f"Invalid magic number: {hex(magic)}")
        length = int.from_bytes(data[4:8], 'big')
        if len(data) < 8 + length:
            raise ValueError("Incomplete frame")
        json_data = data[8:8+length].decode('utf-8')
        obj = json.loads(json_data)
        msg = cls(
            version=obj.get("version", "1.0"),
            type=MessageType(obj["type"]),
            correlation_id=obj["correlation_id"],
            timestamp=obj["timestamp"],
            operation=StateTransition(obj["operation"]),
            payload=obj.get("payload", {}),
            seal=obj.get("seal"),
            public_key=obj.get("public_key"),
            retry_count=obj.get("retry_count", 0),
            idempotency_key=obj.get("idempotency_key"),
        )
        return protocol, msg

    def sign(self, private_key: "ed25519.Ed25519PrivateKey") -> None:
        """Sign the message payload with Ed25519."""
        # Sign the serialized JSON payload (without seal)
        signable = json.dumps({
            "version": self.version,
            "type": self.type.value,
            "correlation_id": self.correlation_id,
            "timestamp": self.timestamp,
            "operation": self.operation.value,
            "payload": self.payload,
            "public_key": self.public_key,
            "retry_count": self.retry_count,
            "idempotency_key": self.idempotency_key,
        }, separators=(',', ':')).encode('utf-8')
        signature = private_key.sign(signable)
        self.seal = signature.hex()
        self.public_key = private_key.public_key().public_bytes(
            Encoding.Raw, PublicFormat.Raw
        ).hex()

    def verify(self) -> bool:
        """Verify the Ed25519 signature using the public key."""
        if not self.seal or not self.public_key:
            return False
        if not CRYPTO_AVAILABLE:
            return False
        try:
            pub_bytes = bytes.fromhex(self.public_key)
            public_key = ed25519.Ed25519PublicKey.from_public_bytes(pub_bytes)
            signable = json.dumps({
                "version": self.version,
                "type": self.type.value,
                "correlation_id": self.correlation_id,
                "timestamp": self.timestamp,
                "operation": self.operation.value,
                "payload": self.payload,
                "public_key": self.public_key,
                "retry_count": self.retry_count,
                "idempotency_key": self.idempotency_key,
            }, separators=(',', ':')).encode('utf-8')
            public_key.verify(bytes.fromhex(self.seal), signable)
            return True
        except Exception:
            return False


# ── State Machine ──

class PipelineState(Enum):
    INIT = "init"
    CLONED = "cloned"
    CODESPACE = "codespace"
    TEMP_CACHE = "temp_cache"
    MAIN = "main"
    ERROR = "error"
    ROLLBACK = "rollback"


@dataclass
class PipelineContext:
    """Context for a single pipeline execution."""
    state: PipelineState = PipelineState.INIT
    current_operation: Optional[StateTransition] = None
    last_message: Optional[Message] = None
    retry_count: int = 0
    idempotency_map: Dict[str, bool] = field(default_factory=dict)


class X3DFX16FProtocol:
    """
    Protocol handler for pocket‑universe communication.
    Manages framing, signing, state transitions, timeouts, and fallback.
    """

    def __init__(
        self,
        private_key: Optional[Any] = None,
        public_key_hex: Optional[str] = None,
        timeout_ms: float = DEFAULT_TIMEOUT,
        max_retries: int = MAX_RETRIES,
    ):
        self.private_key = private_key
        self.public_key_hex = public_key_hex
        self.timeout = timeout_ms / 1000.0  # seconds
        self.max_retries = max_retries
        self.context = PipelineContext()
        self._fallback_active = False

        if CRYPTO_AVAILABLE and self.private_key is None:
            # Generate ephemeral key if none provided
            self.private_key = ed25519.Ed25519PrivateKey.generate()
            self.public_key_hex = self.private_key.public_key().public_bytes(
                Encoding.Raw, PublicFormat.Raw
            ).hex()

    def create_message(
        self,
        operation: StateTransition,
        payload: Optional[Dict] = None,
        msg_type: MessageType = MessageType.REQUEST,
        idempotency_key: Optional[str] = None,
    ) -> Message:
        """Create a signed message."""
        msg = Message(
            type=msg_type,
            operation=operation,
            payload=payload or {},
            idempotency_key=idempotency_key or str(uuid.uuid4()),
        )
        if self.private_key:
            msg.sign(self.private_key)
        return msg

    def verify_message(self, msg: Message) -> bool:
        """Verify message signature and idempotency."""
        if not msg.verify():
            return False
        # Idempotency check: if we've already processed this key, reject duplicate
        if msg.idempotency_key in self.context.idempotency_map:
            return False
        return True

    def mark_processed(self, msg: Message) -> None:
        """Mark a message as processed (for idempotency)."""
        if msg.idempotency_key:
            self.context.idempotency_map[msg.idempotency_key] = True

    async def send_and_wait(
        self,
        msg: Message,
        send_func: Callable[[bytes], Awaitable[None]],
        recv_func: Callable[[], Awaitable[bytes]],
        protocol: ProtocolType = ProtocolType.X3DF,
    ) -> Tuple[bool, Optional[Message]]:
        """
        Send a message and wait for a response with timeout and retry.
        Returns (success, response_message).
        """
        retry = 0
        while retry <= self.max_retries:
            try:
                frame = msg.to_bytes(protocol)
                await send_func(frame)
                # Wait for response with timeout
                resp_bytes = await asyncio.wait_for(recv_func(), timeout=self.timeout)
                _, resp_msg = Message.from_bytes(resp_bytes)
                # Verify response (optional, but recommended)
                if not self.verify_message(resp_msg):
                    raise ValueError("Invalid response signature")
                self.mark_processed(resp_msg)
                return True, resp_msg
            except asyncio.TimeoutError:
                retry += 1
                if retry > self.max_retries:
                    return False, None
                # Exponential backoff with φ factor
                backoff = self.timeout * (BACKOFF_FACTOR ** retry)
                await asyncio.sleep(backoff)
                # Increment retry count
                msg.retry_count = retry
                # Fallback to X16F if X3DF fails repeatedly
                if retry >= 3 and protocol == ProtocolType.X3DF:
                    protocol = ProtocolType.X16F
                    print(f"⚠️ Falling back to X16F for {msg.correlation_id}")
            except Exception as e:
                return False, None
        return False, None

    async def run_pipeline(
        self,
        send_func: Callable[[bytes], Awaitable[None]],
        recv_func: Callable[[], Awaitable[bytes]],
        initial_payload: Optional[Dict] = None,
    ) -> Dict:
        """
        Execute the full pipeline: clone → codespace → temp_cache → main.
        Returns final result or error.
        """
        state = PipelineState.INIT
        result = {"success": False, "final_state": state.value, "messages": []}

        # Step 1: Clone
        msg = self.create_message(StateTransition.CLONE, initial_payload)
        success, resp = await self.send_and_wait(msg, send_func, recv_func, ProtocolType.X3DF)
        if not success:
            await self._rollback(send_func, recv_func, "clone_failed")
            result["error"] = "Clone failed"
            return result
        state = PipelineState.CLONED
        result["messages"].append({"step": "clone", "response": resp.payload if resp else None})

        # Step 2: Codespace
        msg = self.create_message(StateTransition.CODESPACE, resp.payload if resp else {})
        success, resp = await self.send_and_wait(msg, send_func, recv_func, ProtocolType.X3DF)
        if not success:
            await self._rollback(send_func, recv_func, "codespace_failed")
            result["error"] = "Codespace failed"
            return result
        state = PipelineState.CODESPACE
        result["messages"].append({"step": "codespace", "response": resp.payload if resp else None})

        # Step 3: Temp Cache
        msg = self.create_message(StateTransition.TEMP_CACHE, resp.payload if resp else {})
        success, resp = await self.send_and_wait(msg, send_func, recv_func, ProtocolType.X3DF)
        if not success:
            await self._rollback(send_func, recv_func, "temp_cache_failed")
            result["error"] = "Temp cache failed"
            return result
        state = PipelineState.TEMP_CACHE
        result["messages"].append({"step": "temp_cache", "response": resp.payload if resp else None})

        # Step 4: Commit to Main
        msg = self.create_message(StateTransition.COMMIT, resp.payload if resp else {})
        success, resp = await self.send_and_wait(msg, send_func, recv_func, ProtocolType.X3DF)
        if not success:
            await self._rollback(send_func, recv_func, "commit_failed")
            result["error"] = "Commit failed"
            return result
        state = PipelineState.MAIN
        result["messages"].append({"step": "main", "response": resp.payload if resp else None})
        result["success"] = True
        result["final_state"] = state.value
        return result

    async def _rollback(self, send_func, recv_func, reason: str):
        """Send rollback message and attempt to revert to previous state."""
        rollback_msg = self.create_message(
            StateTransition.ROLLBACK,
            {"reason": reason, "correlation_id": self.context.last_message.correlation_id if self.context.last_message else None}
        )
        # Try to send rollback, but ignore errors (best-effort)
        try:
            await send_func(rollback_msg.to_bytes(ProtocolType.X3DF))
        except Exception:
            pass
        self.context.state = PipelineState.ROLLBACK


# ── Demo / Test ──

async def echo_handler(data: bytes) -> bytes:
    """Simple echo handler for testing."""
    prot, msg = Message.from_bytes(data)
    # Echo back with ACK
    resp = Message(
        type=MessageType.ACK,
        correlation_id=msg.correlation_id,
        operation=msg.operation,
        payload={"echo": msg.payload}
    )
    # Sign with a dummy key (in real use, we'd have a key)
    if CRYPTO_AVAILABLE:
        dummy_key = ed25519.Ed25519PrivateKey.generate()
        resp.sign(dummy_key)
    return resp.to_bytes(prot)


async def test_protocol():
    """Test the protocol with a mock send/recv pair."""
    protocol = X3DFX16FProtocol()
    # Mock send: just call echo_handler and return result
    last_response = None

    async def send_func(data: bytes):
        nonlocal last_response
        last_response = await echo_handler(data)

    async def recv_func() -> bytes:
        while last_response is None:
            await asyncio.sleep(0.01)
        resp = last_response
        last_response = None
        return resp

    # Run a simple clone operation
    msg = protocol.create_message(StateTransition.CLONE, {"repo": "hello_world.py"})
    success, resp = await protocol.send_and_wait(
        msg, send_func, recv_func, ProtocolType.X3DF
    )
    print(f"Clone test: success={success}, response={resp.payload if resp else None}")


if __name__ == "__main__":
    if not CRYPTO_AVAILABLE:
        print("⚠️ cryptography module missing; install with: pip install cryptography", file=sys.stderr)
    asyncio.run(test_protocol())
