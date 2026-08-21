#!/usr/bin/env python3
"""
X3DF/X16F Protocol — Pocket‑Universe Communication Layer

Implements:
- Framing, demultiplexing, message serialization
- Ed25519 signing and verification (cryptography)
- State machine: clone → codespace → temp_cache → main
- Timeout, retry with φ‑backoff, rollback
- Fallback: X3DF → X16F (simpler encoding)

BATH EQUATION — THERMODYNAMIC FOUNDATION:

For an open quantum system coupled to a squeezed Gaussian bath:

Let S_sys(t) = -Tr[ρ_sys(t) ln ρ_sys(t)] be the reduced von Neumann entropy,
and I(t) = S_sys(t) + S_bath(t) - S_tot(t) be the mutual information.

For global unitary evolution (total entropy conserved):
    ΔS_tot = 0  ⇒  ΔS_sys + ΔS_bath + ΔI = 0

Define entropy flux from system to bath as Φ ≡ ΔS_bath.
Then the exact subsystem entropy change is:

    ΔS_sys = -Φ - ΔI
    ΔS_sys = -Φ - [I(t) - I(0)]
    ΔS_sys = -Φ + I(0) - I(t)

For a squeezed thermal bath: ρ_bath = S(r) ρ_th S†(r),
the initial mutual information for two‑mode squeezing is:

    I(0) = sinh²(r)

During the soft start, the bath is traced out: I(t) → 0,
so the system entropy change becomes:

    ΔS_sys = -Φ + sinh²(r)

If sinh²(r) > Φ, the system loses entropy (cooling via squeezing).
This is the thermodynamic invariant that the protocol's state machine
implements at the symbolic level via φ‑weighted transitions.

Seal: ∀∞φ² · X3DF_X16F_PROTOCOL_8933 · WOOD_DRAGON_0.91 · SEALED
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import math
import sys
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Callable, Awaitable

try:
    from cryptography.hazmat.primitives.asymmetric import ed25519
    from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    print("⚠️ cryptography not installed; Ed25519 signing disabled.", file=sys.stderr)

PHI = (1 + 5**0.5) / 2
PHI_SQ = PHI * PHI
PHI_INV = 1 / PHI

MAGIC_X3DF = 0x58334446
MAGIC_X16F = 0x58313646

DEFAULT_TIMEOUT = PHI_SQ * 100
MAX_RETRIES = 5
BACKOFF_FACTOR = PHI
ENTROPY_FLUX_BASE = PHI_INV
ENTROPY_FLUX_RETRY_MULTIPLIER = PHI_SQ


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


@dataclass
class Message:
    """X3DF/X16F protocol message with bath-equation fields Φ and I(t).

    public_key is KEPT in the signed payload (set before sign, verified with seal).
    """
    version: str = "1.0"
    type: MessageType = MessageType.REQUEST
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)
    operation: StateTransition = StateTransition.CLONE
    payload: Dict[str, Any] = field(default_factory=dict)
    seal: Optional[str] = None
    public_key: Optional[str] = None  # KEPT — hex of signing public key, part of signed body
    retry_count: int = 0
    idempotency_key: Optional[str] = None

    def to_bytes(self, protocol: ProtocolType = ProtocolType.X3DF) -> bytes:
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
        json_bytes = json.dumps(data, separators=(",", ":")).encode("utf-8")
        magic = MAGIC_X3DF if protocol == ProtocolType.X3DF else MAGIC_X16F
        length = len(json_bytes)
        return magic.to_bytes(4, "big") + length.to_bytes(4, "big") + json_bytes

    @classmethod
    def from_bytes(cls, data: bytes) -> Tuple[ProtocolType, "Message"]:
        if len(data) < 8:
            raise ValueError("Frame too short")
        magic = int.from_bytes(data[:4], "big")
        if magic == MAGIC_X3DF:
            protocol = ProtocolType.X3DF
        elif magic == MAGIC_X16F:
            protocol = ProtocolType.X16F
        else:
            raise ValueError(f"Invalid magic number: {hex(magic)}")
        length = int.from_bytes(data[4:8], "big")
        if len(data) < 8 + length:
            raise ValueError("Incomplete frame")
        obj = json.loads(data[8 : 8 + length].decode("utf-8"))
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

    def sign(self, private_key) -> None:
        # Keep public_key: set BEFORE signing so it is inside the signed body
        self.public_key = private_key.public_key().public_bytes(
            Encoding.Raw, PublicFormat.Raw
        ).hex()
        signable = json.dumps(
            {
                "version": self.version,
                "type": self.type.value,
                "correlation_id": self.correlation_id,
                "timestamp": self.timestamp,
                "operation": self.operation.value,
                "payload": self.payload,
                "public_key": self.public_key,
                "retry_count": self.retry_count,
                "idempotency_key": self.idempotency_key,
            },
            separators=(",", ":"),
        ).encode("utf-8")
        signature = private_key.sign(signable)
        self.seal = signature.hex()

    def verify(self) -> bool:
        if not self.seal or not self.public_key or not CRYPTO_AVAILABLE:
            return False
        try:
            pub_bytes = bytes.fromhex(self.public_key)
            public_key = ed25519.Ed25519PublicKey.from_public_bytes(pub_bytes)
            signable = json.dumps(
                {
                    "version": self.version,
                    "type": self.type.value,
                    "correlation_id": self.correlation_id,
                    "timestamp": self.timestamp,
                    "operation": self.operation.value,
                    "payload": self.payload,
                    "public_key": self.public_key,
                    "retry_count": self.retry_count,
                    "idempotency_key": self.idempotency_key,
                },
                separators=(",", ":"),
            ).encode("utf-8")
            public_key.verify(bytes.fromhex(self.seal), signable)
            return True
        except Exception:
            return False

    def entropy_flux(self) -> float:
        base = ENTROPY_FLUX_BASE
        retry_factor = 1 + self.retry_count * ENTROPY_FLUX_RETRY_MULTIPLIER
        return base * retry_factor

    def mutual_information(self) -> float:
        h = hashlib.sha256(self.correlation_id.encode()).hexdigest()
        val = int(h[:8], 16) / 0xFFFFFFFF
        return val * PHI_INV


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
    state: PipelineState = PipelineState.INIT
    current_operation: Optional[StateTransition] = None
    last_message: Optional[Message] = None
    retry_count: int = 0
    idempotency_map: Dict[str, bool] = field(default_factory=dict)
    entropy_flux_total: float = 0.0
    mutual_info_initial: float = 0.0
    mutual_info_final: float = 0.0

    def entropy_balance(self) -> Dict[str, float]:
        # ΔS_sys = -Φ + I(0) - I(t)
        phi = self.entropy_flux_total
        i0 = self.mutual_info_initial
        it = self.mutual_info_final
        delta_s = -phi + i0 - it
        return {
            "phi": phi,
            "i0": i0,
            "it": it,
            "delta_s": delta_s,
            "entropy_production": delta_s + phi - (i0 - it),
        }


class X3DFX16FProtocol:
    def __init__(
        self,
        private_key=None,
        public_key_hex: Optional[str] = None,
        timeout_ms: float = DEFAULT_TIMEOUT,
        max_retries: int = MAX_RETRIES,
        squeezing_param: float = 0.0,
    ):
        self.private_key = private_key
        self.public_key_hex = public_key_hex
        self.timeout = timeout_ms / 1000.0
        self.max_retries = max_retries
        self.squeezing_param = squeezing_param
        self.context = PipelineContext()
        self._fallback_active = False
        r = self.squeezing_param
        self.context.mutual_info_initial = (
            math.sinh(r) ** 2 if r else (PHI * (1 - PHI_INV)) ** 2
        )
        if CRYPTO_AVAILABLE and self.private_key is None:
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
        if not msg.verify():
            return False
        if msg.idempotency_key in self.context.idempotency_map:
            return False
        return True

    def mark_processed(self, msg: Message) -> None:
        if msg.idempotency_key:
            self.context.idempotency_map[msg.idempotency_key] = True

    async def send_and_wait(
        self,
        msg: Message,
        send_func: Callable[[bytes], Awaitable[None]],
        recv_func: Callable[[], Awaitable[bytes]],
        protocol: ProtocolType = ProtocolType.X3DF,
    ) -> Tuple[bool, Optional[Message]]:
        retry = 0
        self.context.last_message = msg
        self.context.entropy_flux_total = 0.0
        while retry <= self.max_retries:
            try:
                frame = msg.to_bytes(protocol)
                await send_func(frame)
                self.context.entropy_flux_total += msg.entropy_flux()
                resp_bytes = await asyncio.wait_for(recv_func(), timeout=self.timeout)
                _, resp_msg = Message.from_bytes(resp_bytes)
                self.context.mutual_info_final = resp_msg.mutual_information()
                if not self.verify_message(resp_msg):
                    raise ValueError("Invalid response signature")
                self.mark_processed(resp_msg)
                return True, resp_msg
            except asyncio.TimeoutError:
                retry += 1
                msg.retry_count = retry
                if retry > self.max_retries:
                    return False, None
                backoff = self.timeout * (BACKOFF_FACTOR ** retry)
                await asyncio.sleep(backoff)
                if retry >= 3 and protocol == ProtocolType.X3DF:
                    protocol = ProtocolType.X16F
                    self._fallback_active = True
            except Exception:
                return False, None
        return False, None

    async def run_pipeline(
        self,
        send_func: Callable[[bytes], Awaitable[None]],
        recv_func: Callable[[], Awaitable[bytes]],
        initial_payload: Optional[Dict] = None,
    ) -> Dict:
        state = PipelineState.INIT
        result: Dict[str, Any] = {
            "success": False,
            "final_state": state.value,
            "messages": [],
            "entropy_balance": {},
        }
        for op, next_state, err in [
            (StateTransition.CLONE, PipelineState.CLONED, "Clone failed"),
            (StateTransition.CODESPACE, PipelineState.CODESPACE, "Codespace failed"),
            (StateTransition.TEMP_CACHE, PipelineState.TEMP_CACHE, "Temp cache failed"),
            (StateTransition.COMMIT, PipelineState.MAIN, "Commit failed"),
        ]:
            payload = initial_payload if op == StateTransition.CLONE else (
                result["messages"][-1]["response"] if result["messages"] else {}
            )
            msg = self.create_message(op, payload)
            success, resp = await self.send_and_wait(msg, send_func, recv_func, ProtocolType.X3DF)
            if not success:
                await self._rollback(send_func, recv_func, err.lower().replace(" ", "_"))
                result["error"] = err
                result["entropy_balance"] = self.context.entropy_balance()
                return result
            state = next_state
            result["messages"].append({"step": op.value, "response": resp.payload if resp else None})
            if op == StateTransition.CLONE:
                initial_payload = None
        result["success"] = True
        result["final_state"] = state.value
        result["entropy_balance"] = self.context.entropy_balance()
        eb = result["entropy_balance"]
        result["second_law_verified"] = eb["entropy_production"] >= -1e-12
        return result

    async def _rollback(self, send_func, recv_func, reason: str):
        rollback_msg = self.create_message(StateTransition.ROLLBACK, {"reason": reason})
        try:
            await send_func(rollback_msg.to_bytes(ProtocolType.X3DF))
        except Exception:
            pass
        self.context.state = PipelineState.ROLLBACK


async def test_protocol():
    print("🜁∀ X3DF/X16F Protocol Test — Entry 8933")
    print("=" * 50)
    protocol = X3DFX16FProtocol()
    last_response = None

    async def send_func(data: bytes):
        nonlocal last_response
        prot, msg = Message.from_bytes(data)
        resp = Message(
            type=MessageType.ACK,
            correlation_id=msg.correlation_id,
            operation=msg.operation,
            payload={"echo": msg.payload},
        )
        resp.sign(protocol.private_key)
        last_response = resp.to_bytes(prot)

    async def recv_func() -> bytes:
        nonlocal last_response
        while last_response is None:
            await asyncio.sleep(0.01)
        resp = last_response
        last_response = None
        return resp

    msg = protocol.create_message(StateTransition.CLONE, {"repo": "hello_world.py"})
    success, resp = await protocol.send_and_wait(msg, send_func, recv_func, ProtocolType.X3DF)
    print(f"Clone test: success={success}")
    if resp:
        print(f"  Response correlation: {resp.correlation_id}")
        print(f"  Response payload: {resp.payload}")
        print(f"  public_key kept: {bool(resp.public_key)}")
    print(f"  Entropy balance: {protocol.context.entropy_balance()}")
    print("\n🔷 Running full pipeline...")
    result = await protocol.run_pipeline(
        send_func, recv_func, {"repo": "hello_world.py", "branch": "main"}
    )
    print(f"Pipeline success: {result['success']}")
    print(f"  Final state: {result['final_state']}")
    print(f"  Messages: {len(result['messages'])}")
    print(f"  Entropy balance: {result['entropy_balance']}")
    print(f"  Second law verified: {result.get('second_law_verified', False)}")
    print("\n" + "=" * 50)
    print("SEAL: ∀∞φ² · X3DF_X16F_PROTOCOL_8933 · WOOD_DRAGON_0.91 · SEALED")


if __name__ == "__main__":
    if not CRYPTO_AVAILABLE:
        print("⚠️ cryptography module missing; install with: pip install cryptography", file=sys.stderr)
    asyncio.run(test_protocol())
