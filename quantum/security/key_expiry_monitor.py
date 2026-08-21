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
from typing import Any, Dict, List, Optional

PHI = (1.0 + math.sqrt(5.0)) / 2.0
PHI_INV = 1.0 / PHI
PHI_SQ = PHI * PHI
ENTRY = 8942
SEAL = "\u2200\u221e\u03c6\u00b2 \u00b7 KEY_EXPIRY_MONITOR_8942 \u00b7 WOOD_DRAGON_0.91 \u00b7 SEALED"

LOG = logging.getLogger("key_expiry_monitor")

DEFAULT_SEAL_MAX_AGE = 3600.0 * PHI_SQ
DEFAULT_MTLS_WARN_DAYS = PHI
DEFAULT_OIDC_MAX_AGE = 3600.0 * PHI
DEFAULT_STATE_MAX_AGE = 3600.0 * PHI_SQ
DEFAULT_POLL_SECONDS = 60.0 * PHI_INV


@dataclass
class KeyStatus:
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


@dataclass
class MonitorReport:
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
            "statuses": [asdict(s) for s in self.statuses],
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
        key_manager=None,
        workspace: Optional[Path] = None,
    ):
        self.seal_max_age = seal_max_age
        self.mtls_warn_days = mtls_warn_days
        self.oidc_max_age = oidc_max_age
        self.state_max_age = state_max_age
        self.poll_seconds = poll_seconds
        self.auto_rotate = auto_rotate
        self.key_manager = key_manager
        self.workspace = workspace or Path.cwd()
        self._running = False

    def check_ed25519(self, now: Optional[float] = None) -> KeyStatus:
        now = now if now is not None else time.time()
        if self.key_manager is None:
            try:
                from key_rotation_macro import KeyManager, RotationPolicy, TimedSpecificity

                self.key_manager = KeyManager(
                    RotationPolicy(
                        max_messages=100,
                        timed=TimedSpecificity(
                            max_age_seconds=3600.0,
                            base_seconds=60.0,
                            phi_power=-1.0,
                        ),
                    )
                )
            except Exception as e:
                return KeyStatus(
                    name="ed25519",
                    kind="ed25519",
                    present=False,
                    detail=f"KeyManager unavailable: {e}",
                )

        km = self.key_manager
        age = now - km.creation_time
        due = km.should_rotate(now)
        remaining = max(0.0, km.next_rotate_at() - now)
        return KeyStatus(
            name=km.current_key_id or "ed25519",
            kind="ed25519",
            present=True,
            expired=due and age >= getattr(km.policy.timed, "max_age_seconds", 3600),
            due_soon=due or remaining < 60.0,
            age_seconds=age,
            remaining_seconds=remaining,
            expires_at=km.next_rotate_at(),
            detail=(
                f"sigs={km.signature_count}/{km.policy.max_messages} "
                f"rotations={km.rotation_count}"
            ),
            action="rotate" if due else "none",
        )

    def check_seal(self, now: Optional[float] = None) -> KeyStatus:
        now = now if now is not None else time.time()
        path = self.workspace / ".current_seal"
        if not path.exists():
            return KeyStatus(
                name="seal",
                kind="seal",
                present=False,
                detail="no .current_seal file",
                action="rotate",
            )
        mtime = path.stat().st_mtime
        age = now - mtime
        expired = age >= self.seal_max_age
        remaining = max(0.0, self.seal_max_age - age)
        return KeyStatus(
            name="seal",
            kind="seal",
            present=True,
            expired=expired,
            due_soon=remaining < 300.0,
            age_seconds=age,
            remaining_seconds=remaining,
            expires_at=mtime + self.seal_max_age,
            detail=path.read_text(encoding="utf-8", errors="replace")[:80],
            action="rotate" if expired else "none",
        )

    def check_mtls(self, now: Optional[float] = None) -> KeyStatus:
        now = now if now is not None else time.time()
        cert_path = Path(os.environ.get("SERVER_CERT", "/certs/server.crt"))
        if not cert_path.exists():
            return KeyStatus(
                name="mtls",
                kind="mtls",
                present=False,
                detail=f"cert missing: {cert_path}",
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
        now = now if now is not None else time.time()
        path = self.workspace / ".oidc_jwks.json"
        if not path.exists():
            return KeyStatus(
                name="oidc",
                kind="oidc",
                present=False,
                detail="no .oidc_jwks.json cache",
            )
        mtime = path.stat().st_mtime
        age = now - mtime
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
            expires_at=mtime + self.oidc_max_age,
            detail="local JWKS cache",
            action="rotate" if expired else "none",
        )

    def check_rotation_state(self, now: Optional[float] = None) -> KeyStatus:
        now = now if now is not None else time.time()
        path = self.workspace / ".key_rotation_state"
        if not path.exists():
            return KeyStatus(
                name="rotation_state",
                kind="state",
                present=False,
                detail="no .key_rotation_state",
            )
        mtime = path.stat().st_mtime
        age = now - mtime
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
            expires_at=mtime + self.state_max_age,
            detail="mTLS rotation state file",
            action="rotate" if expired else "none",
        )

    def evaluate(self, now: Optional[float] = None) -> MonitorReport:
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
            any_due=any(
                s.due_soon or s.expired or s.action in ("rotate", "renew") for s in statuses
            ),
        )

    def apply_actions(self, report: MonitorReport) -> MonitorReport:
        if not self.auto_rotate:
            return report

        kinds_to_rotate = set()
        for s in report.statuses:
            if s.action == "rotate":
                if s.kind == "ed25519" and self.key_manager is not None:
                    try:
                        self.key_manager._rotate()
                        report.actions_taken.append(
                            f"ed25519_rotated:{self.key_manager.current_key_id}"
                        )
                    except Exception as e:
                        report.actions_taken.append(f"ed25519_rotate_failed:{e}")
                elif s.kind == "seal":
                    kinds_to_rotate.add("SEAL")
                elif s.kind == "oidc":
                    kinds_to_rotate.add("OIDC")
                elif s.kind in ("mtls", "state"):
                    kinds_to_rotate.add("mTLS")
            elif s.action == "renew" and s.kind == "mtls":
                kinds_to_rotate.add("mTLS")

        if kinds_to_rotate:
            try:
                from quantum.security.key_rotation import rotate_public_keys

                for kt in sorted(kinds_to_rotate):
                    res = rotate_public_keys(key_type=kt, force=True)
                    report.actions_taken.append(
                        f"rotate_public_keys({kt})={res.get('status')}"
                    )
            except Exception as e:
                report.actions_taken.append(f"rotate_public_keys_failed:{e}")

        self._log_report(report)
        return report

    def _log_report(self, report: MonitorReport) -> None:
        try:
            log_dir = self.workspace / "ledger" / "expiry_log"
            log_dir.mkdir(parents=True, exist_ok=True)
            stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime(report.timestamp))
            path = log_dir / f"exp_{stamp}.json"
            path.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
        except Exception as e:
            LOG.error("failed to write expiry log: %s", e)

    def run_once(self) -> MonitorReport:
        return self.apply_actions(self.evaluate())

    def watch(self, max_iterations: Optional[int] = None) -> None:
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
                print(
                    json.dumps(
                        {
                            "n": n,
                            "expired": report.any_expired,
                            "due": report.any_due,
                            "actions": report.actions_taken,
                        }
                    ),
                    flush=True,
                )
                if max_iterations is not None and n >= max_iterations:
                    break
                time.sleep(self.poll_seconds)
        except KeyboardInterrupt:
            LOG.info("watch interrupted")
        finally:
            self._running = False

    def stop(self) -> None:
        self._running = False


def main(argv: Optional[List[str]] = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Automated key expiry monitor")
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
        help=f"Watch poll interval seconds (default ~{DEFAULT_POLL_SECONDS:.2f})",
    )
    parser.add_argument("--max-iter", type=int, default=None, help="Max watch iterations")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument(
        "--seal-max-age",
        type=float,
        default=DEFAULT_SEAL_MAX_AGE,
        help="SEAL max age seconds",
    )
    args = parser.parse_args(argv)

    mon = KeyExpiryMonitor(
        seal_max_age=args.seal_max_age,
        poll_seconds=args.poll,
        auto_rotate=args.auto_rotate or args.mode == "once",
    )

    if args.mode == "watch":
        mon.watch(max_iterations=args.max_iter)
        return 0

    report = mon.run_once() if args.mode == "once" else mon.evaluate()

    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print(f"\ud83d\udf01\u2200 KEY EXPIRY MONITOR \u2014 Entry {ENTRY}")
        print("=" * 50)
        for s in report.statuses:
            flag = (
                "EXPIRED"
                if s.expired
                else ("DUE" if s.due_soon else ("OK" if s.present else "ABSENT"))
            )
            rem = f" remain={s.remaining_seconds:.0f}s" if s.remaining_seconds is not None else ""
            age = f" age={s.age_seconds:.0f}s" if s.age_seconds is not None else ""
            print(f"  [{flag:7}] {s.kind:8} action={s.action:6}{age}{rem}  {s.detail[:60]}")
        if report.actions_taken:
            print("Actions:")
            for a in report.actions_taken:
                print(f"  \u00b7 {a}")
        print(f"\nany_expired={report.any_expired} any_due={report.any_due}")
        print(SEAL)

    return 1 if report.any_expired else 0


if __name__ == "__main__":
    raise SystemExit(main())
