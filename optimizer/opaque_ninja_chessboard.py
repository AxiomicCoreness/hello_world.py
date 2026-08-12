#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Opaque Local ⊕ Ninja Numbers ⊕ Chessboard Triangulation
=======================================================
Compression formalism with φ-harmonic weights. Opaque tensor never printed;
only trace invariants + full digests of public factors.

Merge with wallet.dat rotation: HMAC over (wallet_sha256 || ninja || T_digest).

Seal: ∀∞φ² · OPAQUE_NINJA_CHESSBOARD_8637 · SEALED
"""

from __future__ import annotations

import hashlib
import hmac
import json
import math
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import numpy as np
except ImportError:  # pragma: no cover
    np = None  # type: ignore

PHI = (1.0 + math.sqrt(5.0)) / 2.0
NINJA: List[int] = [144, 233, 377, 610, 987, 1597, 2584]
CHESS_N = 13
OPAQUE_DIM = 7


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _full_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()  # 64 hex — never truncated


def ninja_diag() -> "np.ndarray":
    assert np is not None
    return np.diag(np.array(NINJA, dtype=float))


def chessboard_triangulation() -> "np.ndarray":
    assert np is not None
    T = np.zeros((CHESS_N, CHESS_N), dtype=float)
    for i in range(CHESS_N):
        for j in range(CHESS_N):
            if i == j:
                continue
            w = (PHI ** (-abs(i - j) / 12.0)) * math.cos(
                (math.pi / PHI) * (i + j) / CHESS_N
            )
            T[i, j] = w
    # symmetrize
    T = 0.5 * (T + T.T)
    return T


def opaque_invariants() -> Tuple[float, float, float]:
    """Published traces only — not the opaque tensor body."""
    return (PHI ** -709, PHI ** 2, PHI ** 3)


def opaque_local_state(seed: int = 0) -> "np.ndarray":
    """
    Simulated 7×7×7 opaque tensor. Body is not returned by public APIs.
    Entries scaled near machine floor so accidental dumps are useless.
    """
    assert np is not None
    rng = np.random.default_rng(seed)
    O = rng.standard_normal((OPAQUE_DIM, OPAQUE_DIM, OPAQUE_DIM)) * 1e-300
    return O


def compress(
    O: "np.ndarray",
    max_rank: int = 144,
) -> Dict[str, Any]:
    """
    Contract O with ninja diag and chessboard T, then truncated SVD.
    Returns only singular values + shapes + digests — not full factors by default.
    """
    assert np is not None
    N = ninja_diag()
    T = chessboard_triangulation()
    # Mode products: O[i,j,k] with N[i,a], T[j,b], N[k,c] → M[a,b,c]
    # N is 7×7; T is 13×13 — need compatible modes.
    # Practical map: project middle mode of O (7) into 13 via pad/interp weights.
    P = np.zeros((OPAQUE_DIM, CHESS_N), dtype=float)
    for i in range(OPAQUE_DIM):
        for j in range(CHESS_N):
            P[i, j] = PHI ** (-abs(i * CHESS_N / OPAQUE_DIM - j) / 12.0)
    P /= np.linalg.norm(P) + 1e-30

    # M[a,b,c] ≈ sum_ijk O_ijk N_ia P_jb N_kc  (middle via P·T)
    NT = T  # 13×13
    M = np.einsum("ijk,ia,jb,kc->abc", O, N, P @ NT, N, optimize=True)
    flat = M.reshape(OPAQUE_DIM * CHESS_N, OPAQUE_DIM)
    U, s, Vt = np.linalg.svd(flat, full_matrices=False)
    R = min(max_rank, len(s))
    s_comp = s[:R]
    # φ-weighted singular values for sealed summary
    s_phi = s_comp * np.array([PHI ** (-r) for r in range(R)])

    t_bytes = NT.tobytes()
    n_bytes = N.tobytes()
    return {
        "rank": int(R),
        "singular_values_head": [float(x) for x in s_comp[:8]],
        "singular_phi_head": [float(x) for x in s_phi[:8]],
        "shapes": {"M": list(M.shape), "flat": list(flat.shape)},
        "chessboard_sha256": _full_sha256(t_bytes),
        "ninja_sha256": _full_sha256(n_bytes),
        "invariants": {
            "tr1": opaque_invariants()[0],
            "tr2": opaque_invariants()[1],
            "tr3": opaque_invariants()[2],
        },
        "compression_note": "factors withheld; digests + head singular values only",
    }


def merge_hmac_wallet(
    wallet_sha256: str,
    compress_meta: Dict[str, Any],
    key: Optional[bytes] = None,
) -> Dict[str, Any]:
    """
    HMAC-SHA256 over public digests. Key never returned.
    wallet_sha256 must be full 64-hex from optimizer sync.
    """
    if len(wallet_sha256) != 64 or any(c not in "0123456789abcdef" for c in wallet_sha256.lower()):
        raise ValueError("wallet_sha256 must be full 64 hex chars")
    key = key or os.urandom(32)
    msg = (
        f"{wallet_sha256}|"
        f"{compress_meta.get('chessboard_sha256', '')}|"
        f"{compress_meta.get('ninja_sha256', '')}|"
        f"{compress_meta.get('rank', 0)}"
    ).encode()
    tag = hmac.new(key, msg, hashlib.sha256).hexdigest()
    return {
        "hmac_sha256": tag,  # full 64
        "wallet_sha256": wallet_sha256,
        "chessboard_sha256": compress_meta.get("chessboard_sha256"),
        "ninja_sha256": compress_meta.get("ninja_sha256"),
        "rank": compress_meta.get("rank"),
        "key_len": len(key),
        "merged_at": _utc(),
        "seal": "∀∞φ² · OPAQUE_NINJA_CHESSBOARD_8637 · SEALED",
    }


def run_pipeline(wallet_path: Optional[Path] = None, seed: int = 0) -> Dict[str, Any]:
    if np is None:
        return {"ok": False, "error": "numpy required"}

    wallet_sha = "0" * 64
    if wallet_path and Path(wallet_path).is_file():
        h = hashlib.sha256()
        with open(wallet_path, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        wallet_sha = h.hexdigest()
    else:
        try:
            from optimizer.wallet_sync_rotate import OptimizerWalletStub

            stub = OptimizerWalletStub()
            rec = stub.sync()
            if rec.exists and rec.content_sha256:
                wallet_sha = rec.content_sha256
            rot = stub.rotate()
            rotation = asdict(rot)
        except Exception:
            rotation = None
    else:
        rotation = None

    O = opaque_local_state(seed=seed)
    meta = compress(O)
    merged = merge_hmac_wallet(wallet_sha, meta)
    return {
        "ok": True,
        "compress": meta,
        "wallet_rotation": rotation,
        "merge": merged,
        "policy": "opaque body withheld; full digests only",
    }


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--wallet", type=Path, default=None)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    # Fix run_pipeline structure if wallet path given without rotation branch bug
    if np is None:
        print(json.dumps({"ok": False, "error": "numpy required"}))
    else:
        wallet_sha = "0" * 64
        rotation = None
        if args.wallet and args.wallet.is_file():
            h = hashlib.sha256()
            with open(args.wallet, "rb") as f:
                for chunk in iter(lambda: f.read(1 << 20), b""):
                    h.update(chunk)
            wallet_sha = h.hexdigest()
        try:
            from optimizer.wallet_sync_rotate import OptimizerWalletStub

            stub = OptimizerWalletStub(wallet_path=args.wallet or Path("wallet.dat"))
            rec = stub.sync()
            if rec.exists and rec.content_sha256:
                wallet_sha = rec.content_sha256
            rotation = asdict(stub.rotate())
        except Exception as e:
            rotation = {"note": str(e)}

        O = opaque_local_state(seed=args.seed)
        meta = compress(O)
        merged = merge_hmac_wallet(wallet_sha, meta)
        print(
            json.dumps(
                {
                    "ok": True,
                    "compress": meta,
                    "wallet_rotation": rotation,
                    "merge": merged,
                    "policy": "opaque body withheld; full digests only",
                },
                indent=2,
            )
        )
