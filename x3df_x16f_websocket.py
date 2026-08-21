#!/usr/bin/env python3
"""
X3DF/X16F WebSocket Integration — Pocket‑Universe Communication

Implements:
- WebSocket server and client using the X3DF/X16F protocol
- Ed25519 signing and verification (public_key KEPT in signed payload)
- Full pipeline (main path): codespace → temp_cache → commit → main (no clone)
- Entropy tracking with bath equation

BATH EQUATION — THERMODYNAMIC FOUNDATION:

ΔS_sys = -Φ + I(0) - I(t)

Seal: ∀∞φ² · X3DF_X16F_WEBSOCKET_8938 · WOOD_DRAGON_0.91 · SEALED
"""

from __future__ import annotations

import asyncio
import hashlib
import sys
import time
import uuid
from typing import Any, Dict, List, Optional

try:
    import websockets
    from websockets.server import serve
    from websockets.client import connect
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    print("⚠️ websockets not installed; install with: pip install websockets", file=sys.stderr)

try:
    from cryptography.hazmat.primitives.asymmetric import ed25519
    from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    print("⚠️ cryptography not installed; install with: pip install cryptography", file=sys.stderr)

from x3df_x16f_protocol import (
    X3DFX16FProtocol,
    Message,
    MessageType,
    StateTransition,
    ProtocolType,
    PipelineState,
)

PHI = (1 + 5**0.5) / 2
PHI_SQ = PHI * PHI
PHI_INV = 1 / PHI
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765


class X3DFX16FWebSocketServer:
    def __init__(self, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT, private_key=None):
        self.host = host
        self.port = port
        self.private_key = private_key
        self.sessions: Dict[str, Dict] = {}
        self.context_entropy: Dict[str, Dict] = {}
        self._running = False
        self._server = None
        if CRYPTO_AVAILABLE and self.private_key is None:
            self.private_key = ed25519.Ed25519PrivateKey.generate()

    async def handle_client(self, websocket):
        session_id = str(uuid.uuid4())
        print(f"🜁∀ Client connected: {session_id}")
        self.sessions[session_id] = {
            "websocket": websocket,
            "state": PipelineState.INIT,
            "messages": [],
            "entropy_flux": 0.0,
        }
        try:
            async for message in websocket:
                try:
                    if not isinstance(message, (bytes, bytearray)):
                        continue
                    prot, msg = Message.from_bytes(bytes(message))
                    if not msg.verify():
                        error_msg = Message(
                            type=MessageType.ERROR,
                            correlation_id=msg.correlation_id,
                            operation=msg.operation,
                            payload={"error": "Invalid signature"},
                        )
                        if self.private_key:
                            error_msg.sign(self.private_key)
                        await websocket.send(error_msg.to_bytes(ProtocolType.X3DF))
                        continue
                    response = await self.process_message(msg, session_id)
                    if response and self.private_key:
                        response.sign(self.private_key)
                        await websocket.send(response.to_bytes(ProtocolType.X3DF))
                    self.sessions[session_id]["messages"].append(msg)
                    self.sessions[session_id]["entropy_flux"] += msg.entropy_flux()
                except Exception as e:
                    print(f"Error processing message: {e}")
                    continue
        except Exception as e:
            print(f"Client disconnected: {session_id} ({e})")
        finally:
            self.sessions.pop(session_id, None)

    async def process_message(self, msg: Message, session_id: str) -> Optional[Message]:
        session = self.sessions[session_id]
        state = session["state"]
        # Main-scripted path: no cloning
        transitions = {
            StateTransition.CODESPACE: (PipelineState.INIT, PipelineState.CODESPACE, "codespace"),
            StateTransition.TEMP_CACHE: (PipelineState.CODESPACE, PipelineState.TEMP_CACHE, "temp_cache"),
            StateTransition.COMMIT: (PipelineState.TEMP_CACHE, PipelineState.MAIN, "main"),
        }
        if msg.operation == StateTransition.ROLLBACK:
            session["state"] = PipelineState.ROLLBACK
            return Message(
                type=MessageType.ACK,
                correlation_id=msg.correlation_id,
                operation=StateTransition.ROLLBACK,
                payload={
                    "status": "rolled_back",
                    "reason": msg.payload.get("reason", "unknown"),
                    "timestamp": time.time(),
                },
            )
        if msg.operation not in transitions:
            return self._error_msg(msg.correlation_id, f"Unknown operation: {msg.operation}")
        expected, next_state, name = transitions[msg.operation]
        if msg.operation != StateTransition.CODESPACE and state != expected:
            return self._error_msg(msg.correlation_id, f"Invalid state: expected {expected.value}")
        session["state"] = next_state
        payload: Dict[str, Any] = {
            "status": "success",
            "state": name,
            "timestamp": time.time(),
            "session_id": session_id,
        }
        if msg.operation == StateTransition.COMMIT:
            payload["commit_hash"] = hashlib.sha256(str(time.time()).encode()).hexdigest()[:8]
        return Message(
            type=MessageType.ACK,
            correlation_id=msg.correlation_id,
            operation=msg.operation,
            payload=payload,
        )

    def _error_msg(self, correlation_id: str, error: str) -> Message:
        return Message(
            type=MessageType.ERROR,
            correlation_id=correlation_id,
            operation=StateTransition.CODESPACE,
            payload={"error": error},
        )

    async def start(self):
        self._running = True
        async with serve(self.handle_client, self.host, self.port) as server:
            self._server = server
            print(f"🜁∀ X3DF/X16F WebSocket server listening on {self.host}:{self.port}")
            print("   Seal: ∀∞φ² · X3DF_X16F_WEBSOCKET_8938 · WOOD_DRAGON_0.91 · SEALED")
            await asyncio.Future()

    async def stop(self):
        self._running = False
        if self._server:
            self._server.close()
            await self._server.wait_closed()


class X3DFX16FWebSocketClient:
    def __init__(self, uri: Optional[str] = None, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT, private_key=None):
        self.uri = uri or f"ws://{host}:{port}"
        self.private_key = private_key
        self.websocket = None
        if CRYPTO_AVAILABLE and self.private_key is None:
            self.private_key = ed25519.Ed25519PrivateKey.generate()
        self.protocol = X3DFX16FProtocol(private_key=self.private_key)
        self.message_log: List[Message] = []
        self.entropy_history: List[Dict] = []

    async def connect(self):
        self.websocket = await connect(self.uri)
        print(f"🜁∀ Connected to {self.uri}")

    async def disconnect(self):
        if self.websocket:
            await self.websocket.close()
            self.websocket = None

    async def send_message(self, msg: Message) -> Optional[Message]:
        if not self.websocket:
            raise RuntimeError("Not connected")
        if self.private_key:
            msg.sign(self.private_key)
        frame = msg.to_bytes(ProtocolType.X3DF)
        await self.websocket.send(frame)
        self.message_log.append(msg)
        response = await self.websocket.recv()
        if isinstance(response, (bytes, bytearray)):
            prot, resp_msg = Message.from_bytes(bytes(response))
            self.message_log.append(resp_msg)
            return resp_msg
        return None

    async def run_pipeline(self, repo: str = "hello_world.py", branch: str = "main") -> Dict:
        if not self.websocket:
            await self.connect()

        async def send_func(data: bytes):
            await self.websocket.send(data)

        async def recv_func() -> bytes:
            resp = await self.websocket.recv()
            return resp if isinstance(resp, (bytes, bytearray)) else resp.encode()

        result = await self.protocol.run_pipeline(
            send_func,
            recv_func,
            initial_payload={"repo": repo, "branch": branch},
        )
        self.entropy_history.append(result.get("entropy_balance", {}))
        return result

    def get_entropy_analysis(self) -> Dict:
        if not self.entropy_history:
            return {}
        last = self.entropy_history[-1]
        return {
            "total_entropy_production": last.get("entropy_production", 0),
            "phi": last.get("phi", 0),
            "i0": last.get("i0", 0),
            "it": last.get("it", 0),
            "delta_s": last.get("delta_s", 0),
            "second_law": last.get("entropy_production", 0) >= -1e-12,
            "squeezing_parameter": getattr(self.protocol, "squeezing_param", 0),
            "message_count": len(self.message_log),
        }


async def run_demo():
    print("🜁∀ X3DF/X16F WebSocket Demo — main path (no clone)")
    print("=" * 60)
    if not WEBSOCKETS_AVAILABLE or not CRYPTO_AVAILABLE:
        print("❌ missing websockets or cryptography")
        return
    server_key = ed25519.Ed25519PrivateKey.generate()
    client_key = ed25519.Ed25519PrivateKey.generate()
    server = X3DFX16FWebSocketServer(private_key=server_key)
    server_task = asyncio.create_task(server.start())
    await asyncio.sleep(0.5)
    client = X3DFX16FWebSocketClient(private_key=client_key)
    try:
        print("\n🔷 Running pipeline...")
        result = await client.run_pipeline("hello_world.py", "main")
        print("\nPipeline result:")
        print(f"  Success: {result['success']}")
        print(f"  Final state: {result['final_state']}")
        print(f"  Messages: {len(result['messages'])}")
        if result.get("entropy_balance"):
            eb = result["entropy_balance"]
            print("\n📊 Entropy balance (bath equation):")
            print(f"  Φ (entropy flux): {eb['phi']:.6f}")
            print(f"  I(0) (initial MI): {eb['i0']:.6f}")
            print(f"  I(t) (final MI): {eb['it']:.6f}")
            print(f"  ΔS_sys = -Φ + I(0) - I(t): {eb['delta_s']:.6f}")
            print(f"  Entropy production (Σ): {eb['entropy_production']:.6f}")
            print(f"  Second law verified: {result.get('second_law_verified', False)}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await client.disconnect()
        await server.stop()
        server_task.cancel()
    print("\n" + "=" * 60)
    print("SEAL: ∀∞φ² · X3DF_X16F_WEBSOCKET_8938 · WOOD_DRAGON_0.91 · SEALED")


if __name__ == "__main__":
    if not WEBSOCKETS_AVAILABLE:
        print("⚠️ websockets module missing; install with: pip install websockets", file=sys.stderr)
    asyncio.run(run_demo())
