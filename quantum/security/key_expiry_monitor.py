#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🜁∀ KEY EXPIRY MONITOR — ENTRY 8942

Automated monitoring of key / certificate / seal age with φ-harmonic
thresholds and optional auto-rotation.

Watches:
  - Ed25519 KeyManager (message-count + timed specificity)
  - SEAL file (.current_seal) age
  - mTLS cert notAfter (if cryptography + cert files present)
  - OIDC JWKS local cache age
  - .key_rotation_state age

Modes:
  status   — one-shot report
  watch    — loop at φ-harmonic interval; auto-rotate when due
  once     — evaluate + optional rotate, then exit

Seal: ∀∞φ² · KEY_EXPIRY_MONITOR_8942 · WOOD_DRAGON_0.91 · SEALED
"""

from __future__ import annotations

import argparse
import json
import logging
import math
import os
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ─── Constants ────────────────────────────────────────────────────────
PHI = (1.0 + math.sqrt(5.0)) / 2.0
PHI_INV = 1.0 / PHI
PHI_SQ = PHI * PHI
ENTRY = 8942
SEAL = "∀∞φ² · KEY_EXPIRY_MONITOR_8942 · WOOD_DRAGON_0.91 · SEALED"

LOG = logging.getLogger("key_expiry_monitor")

# Default thresholds (in seconds)
DEFAULT_SEAL_MAX_AGE = 3600.0 * PHI_SQ       # ≈ 2.62 hours
DEFAULT_MTLS_WARN_DAYS = PHI                 # ≈ 2.62 days
DEFAULT_OIDC_MAX_AGE = 3600.0 * PHI          # ≈ 1.62 hours
DEFAULT_STATE_MAX_AGE = 3600.0 * PHI_SQ      # ≈ 2.62 hours
DEFAULT_POLL_SECONDS = 60.0 * PHI_INV        # ≈ 37 seconds


@dataclass
class KeyStatus:
    """Status of a single monitored key/certificate."""
    name: str
    kind: str
    present: bool
    expired: bool = False
    due_soon: bool = False
    age_seconds: Optional[float] = None
    remaining_seconds: Optional[float] = None
    expires_at: Optional[float] = None
    detail: str = ""
    action: str = "none"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MonitorReport:
    """Complete report from a monitor evaluation."""
    timestamp: float
    statuses: List[KeyStatus] = field(default_factory=list)
    any_expired: bool = False
    any_due: bool = False
    actions_taken: List[str] = field(default_factory=list)
    seal: str = SEAL
    entry: int = ENTRY

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "iso": datetime.fromtimestamp(self.timestamp, tz=timezone.utc).isoformat(),
            "any_expired": self.any_expired,
            "any_due": self.any_due,
            "actions_taken": self.actions_taken,
            "statuses": [s.to_dict() for s in self.statuses],
            "seal": self.seal,
            "entry": self.entry,
        }


class KeyExpiryMonitor:
    """Automated key expiry monitor with optional auto-rotation."""

    def __init__(
        self,
        seal_max_age: float = DEFAULT_SEAL_MAX_AGE,
        mtls_warn_days: float = DEFAULT_MTLS_WARN_DAYS,
        oidc_max_age: float = DEFAULT_OIDC_MAX_AGE,
        state_max_age: float = DEFAULT_STATE_MAX_AGE,
        poll_seconds: float = DEFAULT_POLL_SECONDS,
        auto_rotate: bool = False,
        key_manager: Any = None,
        workspace: Optional[Path] = None,
    ):
        self.seal_max_age = seal_max_age
        self.mtls_warn_days = mtls_warn_days
        self.oidc_max_age = oidc_max_age
        self.state_max_age = state_max_age
        self.poll_seconds = poll_seconds
        self.auto_rotate = auto_rotate
        self._key_manager = key_manager
        self.workspace = workspace or Path.cwd()
        self._running = False
        self._crypto_available = False

        # Try to import cryptography
        try:
            import cryptography  # noqa: F401
            self._crypto_available = True
        except ImportError:
            LOG.warning("cryptography not available; mTLS cert parsing disabled")

    @property
    def key_manager(self):
        """Lazy-load the key manager."""
        if self._key_manager is None:
            try:
                from quantum.security.key_rotation import HarnessKeyManager
                self._key_manager = HarnessKeyManager(max_messages=100)
                LOG.info("KeyManager initialised")
            except ImportError:
                # Try fallback to key_rotation_macro
                try:
                    from key_rotation_macro import KeyManager
                    self._key_manager = KeyManager(max_messages=100)
                    LOG.info("KeyManager initialised (fallback)")
                except ImportError:
                    LOG.warning("KeyManager not available; ed25519 checks disabled")
        return self._key_manager

    def _get_file_age(self, path: Path) -> Tuple[bool, float]:
        """Get file age in seconds. Returns (exists, age)."""
        if not path.exists():
            return False, 0.0
        return True, time.time() - path.stat().st_mtime

    def check_ed25519(self, now: Optional[float] = None) -> KeyStatus:
        """Check Ed25519 key manager status."""
        now = now if now is not None else time.time()
        km = self.key_manager
        if km is None:
            return KeyStatus(
                name="ed25519",
                kind="ed25519",
                present=False,
                detail="KeyManager unavailable",
            )

        # Try to get age from the manager
        try:
            if hasattr(km, "creation_time"):
                age = now - km.creation_time
            else:
                age = 0.0

            # Check if we have a rotation policy
            max_messages = getattr(km, "max_messages", 100)
            signature_count = getattr(km, "signature_count", 0)
            due = signature_count >= max_messages * 0.8  # 80% threshold

            remaining = max(0.0, (max_messages - signature_count) * 10)  # rough estimate

            return KeyStatus(
                name="ed25519",
                kind="ed25519",
                present=True,
                expired=due and age > 3600,
                due_soon=due or remaining < 60,
                age_seconds=age,
                remaining_seconds=remaining,
                detail=f"sigs={signature_count}/{max_messages}",
                action="rotate" if due else "none",
            )
        except Exception as e:
            return KeyStatus(
                name="ed25519",
                kind="ed25519",
                present=True,
                detail=f"error: {e}",
                action="warn",
            )

    def check_seal(self, now: Optional[float] = None) -> KeyStatus:
        """Check SEAL file age."""
        now = now if now is not None else time.time()
        path = self.workspace / ".current_seal"
        exists, age = self._get_file_age(path)

        if not exists:
            return KeyStatus(
                name="seal",
                kind="seal",
                present=False,
                detail="no .current_seal file",
                action="rotate",
            )

        expired = age >= self.seal_max_age
        remaining = max(0.0, self.seal_max_age - age)

        try:
            content = path.read_text(encoding="utf-8", errors="replace")[:60]
        except Exception:
            content = "unreadable"

        return KeyStatus(
            name="seal",
            kind="seal",
            present=True,
            expired=expired,
            due_soon=remaining < 300.0,
            age_seconds=age,
            remaining_seconds=remaining,
            expires_at=path.stat().st_mtime + self.seal_max_age,
            detail=f"{content}...",
            action="rotate" if expired else "none",
        )

    def check_mtls(self, now: Optional[float] = None) -> KeyStatus:
        """Check mTLS certificate expiry."""
        now = now if now is not None else time.time()
        cert_path = Path(os.environ.get("SERVER_CERT", "/certs/server.crt"))

        if not cert_path.exists():
            return KeyStatus(
                name="mtls",
                kind="mtls",
                present=False,
                detail=f"cert missing: {cert_path}",
            )

        if not self._crypto_available:
            # Fallback: use file mtime as proxy
            exists, age = self._get_file_age(cert_path)
            if not exists:
                return KeyStatus(
                    name="mtls",
                    kind="mtls",
                    present=False,
                    detail=f"cert missing: {cert_path}",
                )
            # Warn if cert file is older than mtls_warn_days
            warn_secs = self.mtls_warn_days * 86400.0
            expired = age >= warn_secs * 2  # double warning age = expired
            due = age >= warn_secs
            return KeyStatus(
                name="mtls",
                kind="mtls",
                present=True,
                expired=expired,
                due_soon=due and not expired,
                age_seconds=age,
                remaining_seconds=max(0.0, warn_secs - age) if due else None,
                detail=f"mtime proxy (cryptography missing)",
                action="renew" if due else "none",
            )

        try:
            from cryptography import x509
            from cryptography.hazmat.backends import default_backend

            pem = cert_path.read_bytes()
            cert = x509.load_pem_x509_certificate(pem, default_backend())
            not_after = getattr(cert, "not_valid_after_utc", None)
            if not_after is None:
                not_after = cert.not_valid_after.replace(tzinfo=timezone.utc)
            exp_ts = not_after.timestamp()
            remaining = exp_ts - now
            warn_secs = self.mtls_warn_days * 86400.0
            expired = remaining <= 0
            due = remaining <= warn_secs

            return KeyStatus(
                name="mtls",
                kind="mtls",
                present=True,
                expired=expired,
                due_soon=due and not expired,
                age_seconds=None,
                remaining_seconds=remaining,
                expires_at=exp_ts,
                detail=f"notAfter={not_after.isoformat()}",
                action="renew" if (expired or due) else "none",
            )
        except Exception as e:
            return KeyStatus(
                name="mtls",
                kind="mtls",
                present=True,
                detail=f"parse error: {e}",
                action="warn",
            )

    def check_oidc(self, now: Optional[float] = None) -> KeyStatus:
        """Check OIDC JWKS cache age."""
        now = now if now is not None else time.time()
        path = self.workspace / ".oidc_jwks.json"

        if not path.exists():
            return KeyStatus(
                name="oidc",
                kind="oidc",
                present=False,
                detail="no .oidc_jwks.json cache",
            )

        exists, age = self._get_file_age(path)
        if not exists:
            return KeyStatus(
                name="oidc",
                kind="oidc",
                present=False,
                detail="cache missing",
                action="rotate",
            )

        expired = age >= self.oidc_max_age
        remaining = max(0.0, self.oidc_max_age - age)

        return KeyStatus(
            name="oidc",
            kind="oidc",
            present=True,
            expired=expired,
            due_soon=remaining < 300.0,
            age_seconds=age,
            remaining_seconds=remaining,
            expires_at=path.stat().st_mtime + self.oidc_max_age,
            detail="local JWKS cache",
            action="rotate" if expired else "none",
        )

    def check_rotation_state(self, now: Optional[float] = None) -> KeyStatus:
        """Check rotation state file age."""
        now = now if now is not None else time.time()
        path = self.workspace / ".key_rotation_state"

        if not path.exists():
            return KeyStatus(
                name="rotation_state",
                kind="state",
                present=False,
                detail="no .key_rotation_state",
            )

        exists, age = self._get_file_age(path)
        if not exists:
            return KeyStatus(
                name="rotation_state",
                kind="state",
                present=False,
                detail="state file missing",
                action="rotate",
            )

        expired = age >= self.state_max_age
        remaining = max(0.0, self.state_max_age - age)

        return KeyStatus(
            name="rotation_state",
            kind="state",
            present=True,
            expired=expired,
            due_soon=remaining < 300.0,
            age_seconds=age,
            remaining_seconds=remaining,
            expires_at=path.stat().st_mtime + self.state_max_age,
            detail="rotation state file",
            action="rotate" if expired else "none",
        )

    def evaluate(self, now: Optional[float] = None) -> MonitorReport:
        """Evaluate all monitored keys and return a report."""
        now = now if now is not None else time.time()
        statuses = [
            self.check_ed25519(now),
            self.check_seal(now),
            self.check_mtls(now),
            self.check_oidc(now),
            self.check_rotation_state(now),
        ]

        return MonitorReport(
            timestamp=now,
            statuses=statuses,
            any_expired=any(s.expired for s in statuses),
            any_due=any(s.due_soon or s.expired or s.action in ("rotate", "renew") for s in statuses),
        )

    def apply_actions(self, report: MonitorReport) -> MonitorReport:
        """Apply auto-rotation actions if enabled."""
        if not self.auto_rotate:
            return report

        kinds_to_rotate = set()
        for s in report.statuses:
            if s.action in ("rotate", "renew"):
                if s.kind == "ed25519" and self._key_manager is not None:
                    try:
                        if hasattr(self._key_manager, "_rotate"):
                            self._key_manager._rotate()
                            report.actions_taken.append(
                                f"ed25519_rotated:{getattr(self._key_manager, 'current_key_id', 'unknown')}"
                            )
                        else:
                            report.actions_taken.append("ed25519_rotate_skipped:no_method")
                    except Exception as e:
                        report.actions_taken.append(f"ed25519_rotate_failed:{e}")
                elif s.kind == "seal":
                    kinds_to_rotate.add("SEAL")
                elif s.kind == "oidc":
                    kinds_to_rotate.add("OIDC")
                elif s.kind in ("mtls", "state"):
                    kinds_to_rotate.add("mTLS")

        if kinds_to_rotate:
            try:
                from quantum.security.key_rotation import rotate_public_keys
                for kt in sorted(kinds_to_rotate):
                    res = rotate_public_keys(key_type=kt, force=True)
                    status = res.get("status") if isinstance(res, dict) else str(res)
                    report.actions_taken.append(f"rotate_public_keys({kt})={status}")
            except ImportError as e:
                report.actions_taken.append(f"rotate_public_keys_import_failed:{e}")
            except Exception as e:
                report.actions_taken.append(f"rotate_public_keys_failed:{e}")

        self._log_report(report)
        return report

    def _log_report(self, report: MonitorReport) -> None:
        """Log the report to the ledger (append-only)."""
        try:
            log_dir = self.workspace / "ledger" / "expiry_log"
            log_dir.mkdir(parents=True, exist_ok=True)
            stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime(report.timestamp))
            path = log_dir / f"exp_{stamp}.json"
            path.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
            LOG.info(f"Report logged to {path}")
        except Exception as e:
            LOG.error("failed to write expiry log: %s", e)

    def run_once(self) -> MonitorReport:
        """Run a single evaluation and apply actions."""
        return self.apply_actions(self.evaluate())

    def status(self) -> MonitorReport:
        """Alias for evaluate() - returns a report without actions."""
        return self.evaluate()

    def watch(self, max_iterations: Optional[int] = None) -> None:
        """Watch loop - runs continuously at poll interval."""
        self._running = True
        n = 0
        LOG.info(
            "key expiry watch started poll=%.2fs auto_rotate=%s",
            self.poll_seconds,
            self.auto_rotate,
        )
        try:
            while self._running:
                report = self.run_once()
                n += 1
                summary = {
                    "n": n,
                    "expired": report.any_expired,
                    "due": report.any_due,
                    "actions": report.actions_taken,
                    "timestamp": datetime.fromtimestamp(report.timestamp, tz=timezone.utc).isoformat(),
                }
                print(json.dumps(summary), flush=True)
                if max_iterations is not None and n >= max_iterations:
                    break
                time.sleep(self.poll_seconds)
        except KeyboardInterrupt:
            LOG.info("watch interrupted")
        finally:
            self._running = False

    def stop(self) -> None:
        """Stop the watch loop."""
        self._running = False


# ─── CLI ──────────────────────────────────────────────────────────────
def main(argv: Optional[List[str]] = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(
        description="Automated key expiry monitor",
        epilog=f"Seal: {SEAL}\nEntry: {ENTRY}",
    )
    parser.add_argument(
        "mode",
        nargs="?",
        choices=["status", "once", "watch"],
        default="status",
        help="status=report only; once=evaluate+act; watch=loop",
    )
    parser.add_argument("--auto-rotate", action="store_true", help="Trigger rotation when due")
    parser.add_argument(
        "--poll",
        type=float,
        default=DEFAULT_POLL_SECONDS,
        help=f"Watch poll interval seconds (default {DEFAULT_POLL_SECONDS:.2f})",
    )
    parser.add_argument("--max-iter", type=int, default=None, help="Max watch iterations")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument(
        "--seal-max-age",
        type=float,
        default=DEFAULT_SEAL_MAX_AGE,
        help=f"SEAL max age seconds (default {DEFAULT_SEAL_MAX_AGE:.0f})",
    )
    parser.add_argument(
        "--oidc-max-age",
        type=float,
        default=DEFAULT_OIDC_MAX_AGE,
        help=f"OIDC JWKS max age seconds (default {DEFAULT_OIDC_MAX_AGE:.0f})",
    )
    parser.add_argument(
        "--state-max-age",
        type=float,
        default=DEFAULT_STATE_MAX_AGE,
        help=f"State file max age seconds (default {DEFAULT_STATE_MAX_AGE:.0f})",
    )
    args = parser.parse_args(argv)

    mon = KeyExpiryMonitor(
        seal_max_age=args.seal_max_age,
        oidc_max_age=args.oidc_max_age,
        state_max_age=args.state_max_age,
        poll_seconds=args.poll,
        auto_rotate=args.auto_rotate or args.mode == "once",
    )

    if args.mode == "watch":
        mon.watch(max_iterations=args.max_iter)
        return 0

    if args.mode == "once":
        report = mon.run_once()
    else:
        report = mon.status()

    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print(f"\n🜁∀ KEY EXPIRY MONITOR — Entry {ENTRY}")
        print("=" * 55)
        for s in report.statuses:
            flag = "EXPIRED" if s.expired else ("DUE" if s.due_soon else ("OK" if s.present else "ABSENT"))
            rem = f" remain={s.remaining_seconds:.0f}s" if s.remaining_seconds is not None else ""
            age = f" age={s.age_seconds:.0f}s" if s.age_seconds is not None else ""
            print(f"  [{flag:7}] {s.kind:12} action={s.action:6}{age}{rem}  {s.detail[:50]}")
        if report.actions_taken:
            print("\nActions taken:")
            for a in report.actions_taken:
                print(f"  · {a}")
        print(f"\n  any_expired={report.any_expired}  any_due={report.any_due}")
        print("=" * 55)
        print(f"  Seal: {SEAL}")
        print(f"  Entry: {ENTRY}")

    return 1 if report.any_expired else 0


if __name__ == "__main__":
    raise SystemExit(main())
