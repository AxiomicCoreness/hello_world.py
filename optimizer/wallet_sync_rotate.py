#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Optimizer stub — wallet.dat sync + rotate
=========================================
Treats wallet.dat as an **opaque local state blob** (path configurable).

- sync: full SHA-256 of file bytes + size + mtime (never prints key material)
- rotate: φ-harmonic session material; only fingerprints / lengths exported

Policy: immutable digests, no secrets in logs/metrics/JSON public fields.

Seal: ∀∞φ² · OPTIMIZER_WALLET_SYNC_ROTATE_8636 · SEALED
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import math
import os
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

PHI = (1.0 + math.sqrt(5.0)) / 2.0
DEFAULT_WALLET = Path(os.environ.get("WALLET_DAT_PATH", "wallet.dat"))
STATE_PATH = Path(os.environ.get("OPTIMIZER_STATE", "/tmp/optimizer_wallet_state.json"))


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()  # full 64 hex — never truncated


@dataclass
class SyncRecord:
    path: str
    exists: bool
    size_bytes: int = 0
    mtime_unix: float = 0.0
    content_sha256: str = ""
    synced_at: str = field(default_factory=_utc)


@dataclass
class RotationRecord:
    index: int
    material_sha256: str  # full hash of rotated material
    material_len: int
    rotated_at: str = field(default_factory=_utc)
    seal: str = ""


class OptimizerWalletStub:
    """Sync opaque wallet.dat + rotate session material (fingerprints only)."""

    def __init__(
        self,
        wallet_path: Path = DEFAULT_WALLET,
        state_path: Path = STATE_PATH,
        master_seed: Optional[bytes] = None,
    ):
        self.wallet_path = Path(wallet_path)
        self.state_path = Path(state_path)
        self.master_seed = master_seed or os.urandom(32)
        self.rotation_count = 0
        self.last_sync: Optional[SyncRecord] = None
        self.history: List[Dict[str, Any]] = []
        self._load()

    def _load(self) -> None:
        if not self.state_path.is_file():
            return
        try:
            data = json.loads(self.state_path.read_text(encoding="utf-8"))
            self.rotation_count = int(data.get("rotation_count", 0))
            self.history = list(data.get("history", []))[-64:]
            ls = data.get("last_sync")
            if ls:
                self.last_sync = SyncRecord(**ls)
            # master_seed never persisted as plaintext; only length marker
        except Exception:
            pass

    def _save(self) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "rotation_count": self.rotation_count,
            "last_sync": asdict(self.last_sync) if self.last_sync else None,
            "history": self.history[-64:],
            "seed_len": len(self.master_seed),
            "policy": "full digests; no secret bytes in state file",
            "updated_at": _utc(),
            "seal": f"∀∞φ² · OPTIMIZER_WALLET · {self.rotation_count}_SEALED",
        }
        self.state_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def sync(self) -> SyncRecord:
        p = self.wallet_path
        if not p.is_file():
            rec = SyncRecord(path=str(p), exists=False)
            self.last_sync = rec
            self._save()
            return rec
        st = p.stat()
        digest = _sha256_file(p)
        rec = SyncRecord(
            path=str(p.resolve()),
            exists=True,
            size_bytes=int(st.st_size),
            mtime_unix=float(st.st_mtime),
            content_sha256=digest,
        )
        self.last_sync = rec
        self._save()
        return rec

    def _derive_material(self, index: int) -> bytes:
        msg = f"wallet-rotate:{index}:{PHI}:{time.time_ns()}".encode()
        return hmac.new(self.master_seed, msg, hashlib.sha256).digest()

    def rotate(self) -> RotationRecord:
        self.rotation_count += 1
        material = self._derive_material(self.rotation_count)
        digest = hashlib.sha256(material).hexdigest()  # full 64
        rec = RotationRecord(
            index=self.rotation_count,
            material_sha256=digest,
            material_len=len(material),
            seal=f"∀∞φ² · OPTIMIZER_ROTATE · {self.rotation_count}_SEALED",
        )
        # Public history: fingerprints only
        self.history.append(
            {
                "index": rec.index,
                "material_sha256": rec.material_sha256,
                "material_len": rec.material_len,
                "rotated_at": rec.rotated_at,
                "seal": rec.seal,
            }
        )
        self._save()
        # material intentionally not returned to callers of public API
        return rec

    def status(self) -> Dict[str, Any]:
        return {
            "wallet_path": str(self.wallet_path),
            "last_sync": asdict(self.last_sync) if self.last_sync else None,
            "rotation_count": self.rotation_count,
            "history_len": len(self.history),
            "last_rotation": self.history[-1] if self.history else None,
            "policy": "immutable full digests; secrets never exported",
        }


def main() -> None:
    ap = argparse.ArgumentParser(description="Optimizer stub: wallet.dat sync + rotate")
    ap.add_argument("--wallet", type=Path, default=DEFAULT_WALLET)
    ap.add_argument("--state", type=Path, default=STATE_PATH)
    ap.add_argument("--sync", action="store_true")
    ap.add_argument("--rotate", action="store_true")
    ap.add_argument("--status", action="store_true")
    args = ap.parse_args()
    stub = OptimizerWalletStub(wallet_path=args.wallet, state_path=args.state)
    out: Dict[str, Any] = {}
    if args.sync or not (args.rotate or args.status):
        out["sync"] = asdict(stub.sync())
    if args.rotate:
        out["rotate"] = asdict(stub.rotate())
    if args.status:
        out["status"] = stub.status()
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
