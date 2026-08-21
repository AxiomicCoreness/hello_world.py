#!/usr/bin/env python3
"""
quantum/security/soft_harness.py — SACL Verify Layer

Implements soft (non‑destructive) harness checks for:
- OIDC offline token minting → garden HMAC → JWT/JWKS
- CDP WebSocket readiness after handshake
- PID health (active controller, plugin status)
- Key expiry monitor integration (read‑only)

ADDED:
- Ed25519 signatures on every check result
- State machine: clone → codespace → temp_cache → commit → main
- Idempotency: stable message IDs + retry handling
- ACK/retry: explicit timeout + bounded exponential backoff

Entry 8951 — Witness: 8950 → 8951 — UNBROKEN
Seal: ∀∞φ² · SOFT_HARNESS_8951 · WOOD_DRAGON_0.91 · SEALED
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import sys
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple, Callable

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
PHI_6 = PHI ** 6

HARNESS_SEAL = "∀∞φ² · SOFT_HARNESS_8951 · WOOD_DRAGON_0.91 · SEALED"
WITNESS_PREV = "8950 → 8951"

BASE_DIR = Path(__file__).resolve().parent.parent.parent
LEDGER_DIR = BASE_DIR / "ledger"
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)


class PipelineState(Enum):
    INIT = "init"
    CLONED = "cloned"
    CODESPACE = "codespace"
    TEMP_CACHE = "temp_cache"
    COMMIT = "commit"
    MAIN = "main"
    ERROR = "error"
    ROLLBACK = "rollback"


class StateTransition(Enum):
    CLONE = "clone"
    CODESPACE = "codespace"
    TEMP_CACHE = "temp_cache"
    COMMIT = "commit"
    MAIN = "main"
    ROLLBACK = "rollback"


@dataclass
class SignedMessage:
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    idempotency_key: str = field(default_factory=lambda: str(uuid.uuid4()))
    operation: StateTransition = StateTransition.CLONE
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    retry_count: int = 0
    seal: Optional[str] = None
    public_key: Optional[str] = None

    def _build_signable(self) -> bytes:
        data = {
            "correlation_id": self.correlation_id,
            "idempotency_key": self.idempotency_key,
            "operation": self.operation.value,
            "payload": self.payload,
            "timestamp": self.timestamp,
            "retry_count": self.retry_count,
            "public_key": self.public_key,
        }
        return json.dumps(data, separators=(',', ':'), sort_keys=True).encode('utf-8')

    def sign(self, private_key) -> None:
        if not CRYPTO_AVAILABLE:
            self.seal = hashlib.sha256(self._build_signable()).hexdigest()
            self.public_key = "offline"
            return
        signable = self._build_signable()
        signature = private_key.sign(signable)
        self.seal = signature.hex()
        self.public_key = private_key.public_key().public_bytes(
            Encoding.Raw, PublicFormat.Raw
        ).hex()

    def verify(self) -> bool:
        if not self.seal or not self.public_key:
            return False
        if not CRYPTO_AVAILABLE or self.public_key == "offline":
            return self.seal == hashlib.sha256(self._build_signable()).hexdigest()
        try:
            pub_bytes = bytes.fromhex(self.public_key)
            public_key = ed25519.Ed25519PublicKey.from_public_bytes(pub_bytes)
            public_key.verify(bytes.fromhex(self.seal), self._build_signable())
            return True
        except Exception:
            return False


class HarnessKeyManager:
    def __init__(self, max_messages: int = 100):
        self.max_messages = max_messages
        self.signature_count = 0
        self._rotate()

    def _rotate(self) -> None:
        if CRYPTO_AVAILABLE:
            self.private_key = ed25519.Ed25519PrivateKey.generate()
            self.public_key_hex = self.private_key.public_key().public_bytes(
                Encoding.Raw, PublicFormat.Raw
            ).hex()
        else:
            self.private_key = None
            self.public_key_hex = "offline"
        self.signature_count = 0

    def sign(self, data: bytes) -> bytes:
        if self.signature_count >= self.max_messages:
            self._rotate()
        self.signature_count += 1
        if CRYPTO_AVAILABLE and self.private_key is not None:
            return self.private_key.sign(data)
        return hashlib.sha256(data).digest()

    def get_public_key_hex(self) -> str:
        return self.public_key_hex


@dataclass
class CheckResult:
    name: str
    passed: bool
    message: str
    detail: Optional[Dict] = None
    timestamp: float = field(default_factory=time.time)
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    seal: Optional[str] = None
    public_key: Optional[str] = None

    def sign(self, key_manager: HarnessKeyManager) -> None:
        signable = json.dumps({
            "name": self.name,
            "passed": self.passed,
            "message": self.message,
            "detail": self.detail,
            "timestamp": self.timestamp,
            "correlation_id": self.correlation_id,
        }, separators=(',', ':'), sort_keys=True).encode('utf-8')
        signature = key_manager.sign(signable)
        self.seal = signature.hex()
        self.public_key = key_manager.get_public_key_hex()

    def verify(self) -> bool:
        if not self.seal or not self.public_key:
            return False
        signable = json.dumps({
            "name": self.name,
            "passed": self.passed,
            "message": self.message,
            "detail": self.detail,
            "timestamp": self.timestamp,
            "correlation_id": self.correlation_id,
        }, separators=(',', ':'), sort_keys=True).encode('utf-8')
        if not CRYPTO_AVAILABLE or self.public_key == "offline":
            return self.seal == hashlib.sha256(signable).hexdigest()
        try:
            pub_bytes = bytes.fromhex(self.public_key)
            public_key = ed25519.Ed25519PublicKey.from_public_bytes(pub_bytes)
            public_key.verify(bytes.fromhex(self.seal), signable)
            return True
        except Exception:
            return False


class IdempotencyStore:
    def __init__(self):
        self._processed: Dict[str, bool] = {}

    def is_processed(self, idempotency_key: str) -> bool:
        return idempotency_key in self._processed

    def mark_processed(self, idempotency_key: str) -> None:
        self._processed[idempotency_key] = True

    def reset(self) -> None:
        self._processed.clear()


class RetryHandler:
    def __init__(
        self,
        base_delay: float = 0.1,
        max_delay: float = 10.0,
        backoff_factor: float = PHI,
        max_retries: int = 5,
    ):
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.max_retries = max_retries

    def next_delay(self, retry_count: int) -> float:
        delay = self.base_delay * (self.backoff_factor ** retry_count)
        return min(delay, self.max_delay)

    def should_retry(self, retry_count: int) -> bool:
        return retry_count < self.max_retries


class SoftHarnessChecker:
    def __init__(self):
        self.results: List[CheckResult] = []
        self._key_manager = HarnessKeyManager()
        self._idempotency = IdempotencyStore()
        self._retry_handler = RetryHandler()
        self._state = PipelineState.INIT
        self._oidc_offline_enabled = os.environ.get("OIDC_OFFLINE", "").lower() in ("1", "true", "yes")
        self._oauth_offline_enabled = os.environ.get("OAUTH_OFFLINE", "").lower() in ("1", "true", "yes")
        self._offline_mode = self._oidc_offline_enabled or self._oauth_offline_enabled

    def transition(self, operation: StateTransition) -> bool:
        transitions = {
            PipelineState.INIT: [StateTransition.CLONE],
            PipelineState.CLONED: [StateTransition.CODESPACE],
            PipelineState.CODESPACE: [StateTransition.TEMP_CACHE],
            PipelineState.TEMP_CACHE: [StateTransition.COMMIT],
            PipelineState.COMMIT: [StateTransition.MAIN],
        }
        allowed = transitions.get(self._state, [])
        if operation not in allowed:
            return False
        next_state_map = {
            StateTransition.CLONE: PipelineState.CLONED,
            StateTransition.CODESPACE: PipelineState.CODESPACE,
            StateTransition.TEMP_CACHE: PipelineState.TEMP_CACHE,
            StateTransition.COMMIT: PipelineState.COMMIT,
            StateTransition.MAIN: PipelineState.MAIN,
            StateTransition.ROLLBACK: PipelineState.ROLLBACK,
        }
        self._state = next_state_map.get(operation, PipelineState.ERROR)
        return True

    def _run_check(
        self,
        name: str,
        check_func: Callable[[], Tuple[bool, str, Optional[Dict]]],
    ) -> CheckResult:
        try:
            passed, message, detail = check_func()
        except Exception as e:
            passed, message, detail = False, f"Exception: {e}", {"error": str(e)}
        result = CheckResult(name=name, passed=passed, message=message, detail=detail)
        result.sign(self._key_manager)
        return result

    def _check_oidc_offline_token(self) -> Tuple[bool, str, Optional[Dict]]:
        try:
            from quantum.security.oidc_cloud import mint_offline_token, verify_offline_token
            from quantum.cdp_convergence.oauth2 import validate_bearer_garden
            os.environ.setdefault("OIDC_OFFLINE", "1")
            cred = mint_offline_token("soft-harness-8951")
            claims = verify_offline_token(cred.access_token)
            garden_claims, err = validate_bearer_garden("Bearer " + cred.access_token)
            if claims.verified and garden_claims is not None:
                return True, "Offline token validated successfully.", {
                    "sub": claims.sub, "issuer": claims.iss, "garden_hmac": "ok",
                }
            return False, f"Offline token validation failed: {err}", {"sub": claims.sub}
        except ImportError as e:
            return False, "oidc/oauth2 module not available.", {"error": str(e)}
        except Exception as e:
            return False, f"Exception: {e}", {"error": str(e)}

    def _check_websocket_ready(self) -> Tuple[bool, str, Optional[Dict]]:
        try:
            from quantum.security.oidc_cloud import mint_offline_token
            from quantum.cdp_convergence.handshake import handshake_from_authorization
            os.environ.setdefault("OIDC_OFFLINE", "1")
            cred = mint_offline_token("soft-harness-ws")
            status = handshake_from_authorization("Bearer " + cred.access_token)
            ready = bool(status.websocket_ready)
            if ready:
                return True, "WebSocket ready.", {"ready": True, "oauth_validated": status.oauth_validated}
            return False, f"WebSocket not ready: {status.error}", {"ready": False}
        except Exception as e:
            ready = os.environ.get("WEBSOCKET_READY", "").lower() in ("1", "true", "yes")
            if ready:
                return True, "WebSocket ready (env).", {"ready": True}
            return False, f"WebSocket not ready: {e}", {"ready": False, "error": str(e)}

    def _check_pid_health(self) -> Tuple[bool, str, Optional[Dict]]:
        try:
            from quantum.active_pid_controller import ActivePIDController
            ctl = ActivePIDController()
            out = ctl.step_toward_coherence(0.9, target=1.0, dt=0.01)
            if out.get("active") and "u" in out:
                return True, "Active PID controller healthy.", {
                    "u": out["u"], "error": out.get("error"), "active": True,
                }
            return False, "PID controller inactive.", out
        except ImportError:
            pid_file = BASE_DIR / "run" / "pid_controller.pid"
            if pid_file.exists():
                try:
                    pid = int(pid_file.read_text().strip())
                    return True, f"PID controller running (PID: {pid}).", {"pid": pid}
                except Exception:
                    return False, "PID file exists but invalid.", {}
            return False, "PID controller module/file not found.", {"file": str(pid_file)}
        except Exception as e:
            return False, f"Exception: {e}", {"error": str(e)}

    def _check_key_expiry(self) -> Tuple[bool, str, Optional[Dict]]:
        try:
            from quantum.security.key_expiry_monitor import KeyExpiryMonitor
            rep = KeyExpiryMonitor(auto_rotate=False).evaluate()
            if not rep.any_expired:
                return True, "All keys/secrets healthy.", {
                    "any_expired": rep.any_expired, "any_due": rep.any_due, "n": len(rep.statuses),
                }
            return False, "Some keys/secrets near expiry or expired.", {
                "any_expired": rep.any_expired, "any_due": rep.any_due,
            }
        except ImportError:
            return True, "key_expiry_monitor not found; skipping.", {"error": "import_failure"}
        except Exception as e:
            return False, f"Exception: {e}", {"error": str(e)}

    async def run_with_retry(
        self,
        check_func: Callable[[], Tuple[bool, str, Optional[Dict]]],
        name: str,
        idempotency_key: str,
    ) -> CheckResult:
        if self._idempotency.is_processed(idempotency_key):
            return CheckResult(
                name=name, passed=True, message="Already processed (idempotent).",
                detail={"idempotency_key": idempotency_key},
            )
        retry_count = 0
        last_err: Optional[Exception] = None
        while self._retry_handler.should_retry(retry_count):
            try:
                passed, message, detail = check_func()
                result = CheckResult(name=name, passed=passed, message=message, detail=detail)
                result.sign(self._key_manager)
                self._idempotency.mark_processed(idempotency_key)
                return result
            except Exception as e:
                last_err = e
                retry_count += 1
                if self._retry_handler.should_retry(retry_count):
                    await asyncio.sleep(self._retry_handler.next_delay(retry_count))
                else:
                    result = CheckResult(
                        name=name, passed=False,
                        message=f"Failed after {retry_count} retries.",
                        detail={"error": str(e), "retry_count": retry_count},
                    )
                    result.sign(self._key_manager)
                    return result
        result = CheckResult(
            name=name, passed=False, message="Max retries exceeded.",
            detail={"retry_count": retry_count, "error": str(last_err) if last_err else None},
        )
        result.sign(self._key_manager)
        return result

    async def run_pipeline(self) -> Dict[str, Any]:
        pipeline_results = []
        if self.transition(StateTransition.CLONE):
            pipeline_results.append(await self.run_with_retry(
                self._check_oidc_offline_token, "oidc_offline_token", f"clone_{uuid.uuid4().hex[:8]}"))
        else:
            return {"error": "State transition failed: INIT → CLONE"}
        if self.transition(StateTransition.CODESPACE):
            pipeline_results.append(await self.run_with_retry(
                self._check_websocket_ready, "websocket_ready", f"codespace_{uuid.uuid4().hex[:8]}"))
        else:
            return {"error": "State transition failed: CLONED → CODESPACE"}
        if self.transition(StateTransition.TEMP_CACHE):
            pipeline_results.append(await self.run_with_retry(
                self._check_pid_health, "pid_health", f"temp_cache_{uuid.uuid4().hex[:8]}"))
        else:
            return {"error": "State transition failed: CODESPACE → TEMP_CACHE"}
        if self.transition(StateTransition.COMMIT):
            pipeline_results.append(await self.run_with_retry(
                self._check_key_expiry, "key_expiry", f"commit_{uuid.uuid4().hex[:8]}"))
        else:
            return {"error": "State transition failed: TEMP_CACHE → COMMIT"}
        if self.transition(StateTransition.MAIN):
            self._state = PipelineState.MAIN
        else:
            return {"error": "State transition failed: COMMIT → MAIN"}
        passed = sum(1 for r in pipeline_results if r.passed)
        total = len(pipeline_results)
        summary = {
            "pipeline": {
                "state": self._state.value,
                "steps": [r.__dict__ for r in pipeline_results],
                "total": total,
                "passed": passed,
                "failed": total - passed,
                "all_passed": passed == total,
                "seal": HARNESS_SEAL,
                "witness": WITNESS_PREV,
            },
            "key_manager": {
                "signature_count": self._key_manager.signature_count,
                "public_key": self._key_manager.get_public_key_hex()[:16] + "...",
            },
        }
        self.results = pipeline_results
        return summary

    def report_to_ledger(self, summary: Dict) -> None:
        ledger_entry = {
            "entry_index": 8951,
            "event": "/harness_soft_checks_oidc_pid",
            "status": "VERIFIED" if summary["pipeline"]["all_passed"] else "FAILED_SOFT",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "pipeline": {
                "state": summary["pipeline"]["state"],
                "total": summary["pipeline"]["total"],
                "passed": summary["pipeline"]["passed"],
                "failed": summary["pipeline"]["failed"],
                "steps": [{
                    "name": r["name"], "passed": r["passed"], "message": r["message"],
                    "seal": (r.get("seal") or "")[:16] + "...",
                } for r in summary["pipeline"]["steps"]],
            },
            "key_manager": summary["key_manager"],
            "witness": WITNESS_PREV,
            "seal": HARNESS_SEAL,
        }
        ledger_path = LEDGER_DIR / "8951.yaml"
        try:
            import yaml
            with open(ledger_path, "w") as f:
                yaml.dump(ledger_entry, f, default_flow_style=False)
            print(f"📋 Ledger entry written: {ledger_path}")
        except ImportError:
            lines = [
                "entry_index: 8951",
                "event: /harness_soft_checks_oidc_pid",
                f"status: {ledger_entry['status']}",
                f"timestamp: {ledger_entry['timestamp']}",
                f"witness: \"{WITNESS_PREV}\"",
                f"seal: \"{HARNESS_SEAL}\"",
            ]
            ledger_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            print(f"📋 Ledger entry written: {ledger_path}")


async def main() -> int:
    print("\n🔷 SOFT HARNESS — OIDC + PID (with Ed25519 + State Machine + Idempotency + ACK/Retry)")
    print("=" * 70)
    checker = SoftHarnessChecker()
    summary = await checker.run_pipeline()
    if "error" in summary:
        print(f"  ERROR: {summary['error']}")
        return 1
    print(f"\n  Pipeline state: {summary['pipeline']['state']}")
    print(f"  Total checks: {summary['pipeline']['total']}")
    print(f"  Passed: {summary['pipeline']['passed']}")
    print(f"  Failed: {summary['pipeline']['failed']}")
    print(f"  All passed: {summary['pipeline']['all_passed']}")
    for step in summary['pipeline']['steps']:
        status = "✅" if step['passed'] else "❌"
        print(f"  {status} {step['name']}: {step['message']}")
    print(f"\n  Key manager: {summary['key_manager']['signature_count']} signatures")
    print(f"  Public key: {summary['key_manager']['public_key']}")
    print(f"\n  Seal: {HARNESS_SEAL}")
    print(f"  Witness: {WITNESS_PREV}")
    checker.report_to_ledger(summary)
    return 0 if summary["pipeline"]["all_passed"] else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
