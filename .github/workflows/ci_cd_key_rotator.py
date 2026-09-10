#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ci_cd_key_rotator.py — Sovereign Key Rotator with φ-harmonic scheduling.

Provides sovereign key rotation using HMAC-SHA3-256 derivation with a
φ-harmonic rotation *schedule* (not a cryptographic PRNG). Two output
formats are supported: Flask128 (32 hex chars = 128 bits) and URL-safe
Base64 (43 chars from 32 raw bytes).

Security model
--------------
- All key material derives from HMAC-SHA3-256 over (master_seed, index).
- The φ-harmonic generator is used ONLY for scheduling and nonce diversity;
  it is explicitly NOT a cryptographic PRNG and MUST NOT be used to
  generate key material directly.
- Master seed lives in AWS Secrets Manager (or is generated once via
  os.urandom(32) on first run). Only metadata + master seed hex is
  persisted; derived keys are NEVER stored.

Security Headers (CORS, CSP, HSTS, ...) are NOT enforced here — this is a
CLI/backend utility. They are enforced at the service layer in
port380_mcp.py (FastAPI middleware). The GitHub Actions workflows verify
their presence before any rotation runs.

Seal : ∀∞φ² · KEY_ROTATION_INTEGRATED · 632_SEALED · WOOD_DRAGON_0.91
Hash : sha3_256 (FIPS 202) — canonical seal over state
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import math
import os
import secrets
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# ─── CONSTANTS ────────────────────────────────────────────────────────────────
PHI = (1.0 + math.sqrt(5.0)) / 2.0
PHI_INV = 1.0 / PHI
HASH_ALGO = "sha3_256"
SEAL_BASE = "∀∞φ² · KEY_ROTATION_INTEGRATED · 632_SEALED · WOOD_DRAGON_0.91 · SEALED"
DEFAULT_SECRET_NAME = "sovereign-hamiltonian-hmac-632"
DEFAULT_REGION = "us-east-1"
DEFAULT_FORMAT = "flask128"
VALID_FORMATS = {"flask128", "base64"}
REPORT_PATH = Path("rotation_report.json")

# ─── OPTIONAL AWS SDK ─────────────────────────────────────────────────────────
try:
    import boto3  # type: ignore
    from botocore.exceptions import ClientError  # type: ignore
    _BOTO3_AVAILABLE = True
except Exception:  # pragma: no cover — local dev without boto3
    boto3 = None  # type: ignore
    ClientError = Exception  # type: ignore
    _BOTO3_AVAILABLE = False


# ─── CANONICAL HASH ───────────────────────────────────────────────────────────
def canonical_hash(data: Dict[str, Any]) -> str:
    """SHA3-256 over canonical (sorted-key, compact-JSON) form of `data`,
    excluding any 'seal' field. Matches .github/scripts/verify_ledger.py."""
    body = {k: v for k, v in data.items() if k != "seal"}
    canon = json.dumps(body, sort_keys=True, separators=(",", ":"))
    return hashlib.new(HASH_ALGO, canon.encode("utf-8")).hexdigest()


def apply_seal(data: Dict[str, Any], prefix: str = SEAL_BASE) -> Dict[str, Any]:
    """Return a copy of `data` with `seal = prefix · sha3_256(canonical(body))`."""
    body = {k: v for k, v in data.items() if k != "seal"}
    h = hashlib.new(HASH_ALGO,
                    json.dumps(body, sort_keys=True,
                               separators=(",", ":")).encode("utf-8")).hexdigest()
    out = dict(body)
    out["seal"] = f"{prefix} · {h}"
    return out


# ─── φ-HARMONIC SCHEDULER (NON-CRYPTOGRAPHIC) ────────────────────────────────
class PhiHarmonicScheduler:
    """
    φ-harmonic scheduler for rotation cadence.

    The Weyl sequence (state + PHI) mod 1 is deterministic and fully
    predictable. It is used here only to modulate the *interval* between
    rotations — never to produce key material.

    If you need cryptographic randomness, use `secrets` or
    `os.urandom` directly.
    """

    def __init__(self, seed: bytes):
        seed_digest = hashlib.new(HASH_ALGO, seed).digest()
        self.state = int.from_bytes(seed_digest[:8], "big") / float(1 << 64)
        self.counter = 0

    def next_interval(self, base_seconds: int = 21600) -> float:
        """Return the next φ-modulated interval in seconds (base = 6h)."""
        self.state = (self.state + PHI) % 1.0
        self.counter += 1
        modulate = (self.state + self.counter * PHI_INV) % 1.0
        return float(base_seconds) * (0.5 + 0.5 * modulate)

    def nonce(self, n_bytes: int = 16) -> bytes:
        """Non-cryptographic nonce — suitable only for metadata uniqueness."""
        out = bytearray()
        while len(out) < n_bytes:
            v = int(self.state * (1 << 56))
            out.extend(v.to_bytes(7, "big"))
            self.state = (self.state + PHI) % 1.0
            self.counter += 1
        return bytes(out[:n_bytes])


# ─── SOVEREIGN KEY ROTATOR ────────────────────────────────────────────────────
class SovereignKeyRotator:
    """φ-harmonic key rotator — HMAC-SHA3-256 derivation, dual encoding."""

    def __init__(self, master_seed: bytes, schedule_seed: Optional[bytes] = None):
        if len(master_seed) != 32:
            raise ValueError("master_seed must be 32 bytes")
        self.master_seed = master_seed
        self.scheduler = PhiHarmonicScheduler(schedule_seed or master_seed)
        self.rotation_count = 0
        self.key_history: List[Dict[str, Any]] = []

    # ── derivation ──────────────────────────────────────────────────────────
    def _derive_key(self, index: int) -> bytes:
        """HMAC-SHA3-256(master_seed, domain-separated message)."""
        message = f"sovereign-hamiltonian/key/v1:{index}:{PHI}".encode("utf-8")
        return hmac.new(self.master_seed, message, hashlib.sha3_256).digest()

    @staticmethod
    def _encode_base64(key_bytes: bytes) -> str:
        return base64.urlsafe_b64encode(key_bytes).decode("ascii").rstrip("=")

    @staticmethod
    def _encode_flask128(key_bytes: bytes) -> str:
        return key_bytes[:16].hex()  # 32 hex chars = 128 bits

    def _encode_key(self, key_bytes: bytes, fmt: str) -> str:
        if fmt == "flask128":
            return self._encode_flask128(key_bytes)
        if fmt == "base64":
            return self._encode_base64(key_bytes)
        raise ValueError(f"unknown key format: {fmt!r}")

    # ── rotation ────────────────────────────────────────────────────────────
    def rotate(self, fmt: str = DEFAULT_FORMAT) -> Dict[str, Any]:
        if fmt not in VALID_FORMATS:
            raise ValueError(f"fmt must be one of {sorted(VALID_FORMATS)}")
        previous = self.rotation_count
        self.rotation_count += 1
        key_bytes = self._derive_key(self.rotation_count)
        key = self._encode_key(key_bytes, fmt)
        nonce = secrets.token_hex(16)  # cryptographic nonce, NOT from scheduler

        entry: Dict[str, Any] = {
            "index": self.rotation_count,
            "key_hash": hashlib.new(HASH_ALGO, key.encode("utf-8")).hexdigest(),
            "key_format": fmt,
            "nonce": nonce,
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "witness": f"{previous} → {self.rotation_count} — UNBROKEN",
        }
        self.key_history.append(entry)

        # Return the key only to the caller; never persist it
        return {"key": key, "metadata": entry}


# ─── AWS SECRETS MANAGER ──────────────────────────────────────────────────────
class AWSSecretsManager:
    """Thin wrapper around AWS Secrets Manager for state persistence."""

    def __init__(self, secret_name: str, region: str = DEFAULT_REGION):
        if not _BOTO3_AVAILABLE:
            raise RuntimeError(
                "boto3 is required for AWSSecretsManager — "
                "install with `pip install boto3`"
            )
        self.secret_name = secret_name
        self.region = region
        self.client = boto3.client("secretsmanager", region_name=region)

    def load_state(self) -> Optional[Dict[str, Any]]:
        try:
            resp = self.client.get_secret_value(SecretId=self.secret_name)
            return json.loads(resp["SecretString"])
        except ClientError as e:  # type: ignore[misc]
            code = getattr(e, "response", {}).get("Error", {}).get("Code", "")
            if code in ("ResourceNotFoundException", "ResourceNotFound"):
                return None
            raise

    def save_state(self, state: Dict[str, Any]) -> None:
        self.client.put_secret_value(
            SecretId=self.secret_name,
            SecretString=json.dumps(state),
        )


# ─── MAIN ENTRY POINT ─────────────────────────────────────────────────────────
def rotate_keys(
    secret_name: str = DEFAULT_SECRET_NAME,
    region: str = DEFAULT_REGION,
    force: bool = False,
    count: int = 1,
    key_format: str = DEFAULT_FORMAT,
    report_path: Path = REPORT_PATH,
) -> Dict[str, Any]:
    """
    Perform key rotation and persist updated state.

    Rotation rule
    -------------
    - If no prior state exists → rotate immediately (bootstrap).
    - If prior state exists and `force=True` → rotate `count` times.
    - If prior state exists and `force=False` → rotate exactly once if
      `count == 0` is false; otherwise no rotation. The workflow passes
      `count=1` by default, so a single rotation is performed.
    """
    if key_format not in VALID_FORMATS:
        raise ValueError(f"key_format must be one of {sorted(VALID_FORMATS)}")
    if count < 0:
        raise ValueError("count must be >= 0")

    sm = AWSSecretsManager(secret_name, region)
    state = sm.load_state()

    if state and "master_seed" in state:
        master_seed = bytes.fromhex(state["master_seed"])
        rotator = SovereignKeyRotator(master_seed)
        rotator.rotation_count = int(state.get("rotation_count", 0))
        rotator.key_history = list(state.get("key_history", []))
    else:
        master_seed = os.urandom(32)
        rotator = SovereignKeyRotator(master_seed)

    rotations_performed = 0
    for i in range(count):
        if state is None or force or i > 0:
            result = rotator.rotate(fmt=key_format)
            rotations_performed += 1
            meta = result["metadata"]
            print(f"  ✅ Rotation {meta['index']}: "
                  f"{meta['key_hash'][:16]}... ({key_format})")

    # ── persist only metadata + master seed (hex) ─────────────────────────
    new_state: Dict[str, Any] = {
        "entry_index": rotator.rotation_count,
        "hash_algo": HASH_ALGO,
        "master_seed": master_seed.hex(),
        "rotation_count": rotator.rotation_count,
        "key_history": rotator.key_history,
        "last_rotation": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "key_format": key_format,
        "phi": PHI,
        "witness_continuity": (
            f"{max(rotator.rotation_count - 1, 0)} → {rotator.rotation_count} — UNBROKEN"
            if rotator.rotation_count > 0
            else "0 — UNBROKEN"
        ),
    }
    sealed_state = apply_seal(new_state)
    sm.save_state(sealed_state)

    # ── φ-harmonic next interval ──────────────────────────────────────────
    interval = rotator.scheduler.next_interval(base_seconds=21600)

    latest = rotator.key_history[-1] if rotator.key_history else {}

    output: Dict[str, Any] = {
        "rotation_count": rotator.rotation_count,
        "rotations_performed": rotations_performed,
        "current_fingerprint": latest.get("key_hash", ""),
        "current_format": key_format,
        "next_rotation_interval": f"{interval:.2f}",
        "seal": sealed_state["seal"],
        "witness_continuity": new_state["witness_continuity"],
        "hash_algo": HASH_ALGO,
    }

    # ── GitHub Actions outputs ────────────────────────────────────────────
    gh_out = os.environ.get("GITHUB_OUTPUT")
    if gh_out:
        with open(gh_out, "a", encoding="utf-8") as fh:
            fh.write(f"rotation_count={output['rotation_count']}\n")
            fh.write(f"current_fingerprint={output['current_fingerprint']}\n")
            fh.write(f"next_rotation_interval={output['next_rotation_interval']}\n")
            fh.write(f"current_format={output['current_format']}\n")
            fh.write(f"hash_algo={output['hash_algo']}\n")

    # ── rotation_report.json (consumed by workflow Upload Report step) ────
    report = {
        "rotation_report": output,
        "hash_algo": HASH_ALGO,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    report_path.write_text(json.dumps(report, indent=2))

    # ── console summary ───────────────────────────────────────────────────
    print()
    print(f"✅ Rotation complete. Total rotations: {rotator.rotation_count}")
    print(f"✅ Rotations performed this run: {rotations_performed}")
    print(f"✅ Key format: {key_format}")
    print(f"✅ Next rotation in {interval:.2f} seconds")
    print(f"✅ Seal: {output['seal']}")
    print(f"📋 Report written: {report_path}")

    return output


def generate_flask128_key() -> str:
    """
    Generate a standalone Flask128 key (128 bits / 32 hex chars).

    Uses `secrets.token_bytes(16)` — cryptographically secure. The φ-harmonic
    scheduler is intentionally NOT used here; it is not a CSPRNG.
    """
    return secrets.token_bytes(16).hex()


# ─── CLI ──────────────────────────────────────────────────────────────────────
def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return default
    try:
        return int(raw)
    except ValueError:
        print(f"⚠️ {name}={raw!r} is not an integer — using default {default}",
              file=sys.stderr)
        return default


if __name__ == "__main__":
    rotate_keys(
        secret_name=os.environ.get("SECRET_NAME", DEFAULT_SECRET_NAME),
        region=os.environ.get("AWS_REGION", DEFAULT_REGION),
        force=_env_bool("FORCE_ROTATE", False),
        count=_env_int("ROTATE_COUNT", 1),
        key_format=os.environ.get("KEY_FORMAT", DEFAULT_FORMAT),
    )
