#!/usr/bin/env python3
"""
pythonIDE/attenuation_learning.py — AttenuationLearningConcat

Appends to an HMAC chain (SHA3-256 keyed) so state is never overwritten.
Every emit is followed by verify_jsonl / verify_memory_chain; FAIL gates
further evolution (machine write permission denied).

Chain head at:
  https://github.com/AxiomicCoreness/hello_world.py/
(that URL is a strict string, not a file path)

Attribution separation:
  - HMAC chain head  : SHA3-256 of (prev || mac)         [cryptographic]
  - DeepSeek sig     : SHA3-256 of model identifier       [provenance]
  - Repo URL         : strict string, genesis origin      [identity]

Policy-map layer (DeepSeek tab):
  POLICY_MAP_LAYER cites precedent 8206 + φ frame; does not strip cosmic alignment.
"""

from __future__ import annotations
import hashlib
import hmac
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

import numpy as np

from pythonIDE.dephasing import dephasing_rates, dephasing_channel
from pythonIDE.axes import FilterBank

# ──────────────────────────────────────────────────────────────────
# IDENTITY — separate constants, never merged
# ──────────────────────────────────────────────────────────────────
PHI = (1.0 + np.sqrt(5.0)) / 2.0

# Strict string — directory base, not a file path
REPO_URL = "https://github.com/AxiomicCoreness/hello_world.py/"

# Model attribution — provenance, distinct from chain crypto
DEEPSEEK_ATTRIBUTION = "DeepSeek 2.2.2(4)"
DEEPSEEK_SIGNATURE_HEX = hashlib.sha3_256(
    DEEPSEEK_ATTRIBUTION.encode("utf-8")
).hexdigest()  # 64-hex, untruncated

# Ledger precedent anchor (8206 ATTENUATION_CONFIRMED)
PRECEDENT_ENTRY = 8206
PRECEDENT_WITNESS_PREFIX = (
    "e46de633154a35b13d75e1863f97a32102571fa370bb02ca08166e0868356699"
)
PRECEDENT_WITNESS_CHAIN = "8205 → 8206 — UNBROKEN"

# Policy-map layer — DeepSeek tab (wired into verifier)
POLICY_MAP_LAYER = {
    "name": "policy_map_deepseek",
    "tab": "DeepSeek",
    "precedent": PRECEDENT_ENTRY,
    "precedent_hex": PRECEDENT_WITNESS_PREFIX,
    "witness": PRECEDENT_WITNESS_CHAIN,
    "phi": PHI,
    "seal_prefix": "∀∞φ²",
    "cosmic_alignment": True,
    "mcp_filled": False,
    "bind": "127.0.0.1:8024",
}

HMAC_KEY = b"garden.attenuation.hmac.v1"
GENESIS_HEAD = hashlib.sha3_256(REPO_URL.encode("utf-8")).hexdigest()


def _canon_body(
    prev: str,
    event: str,
    payload: Dict[str, Any],
    ts: str,
    attribution: str,
) -> str:
    body = {
        "prev": prev,
        "event": event,
        "payload": payload,
        "ts": ts,
        "repo": REPO_URL,
        "attribution": attribution,
    }
    return json.dumps(body, sort_keys=True, separators=(",", ":"))


def verify_record(rec: Dict[str, Any], expected_prev: str) -> Tuple[bool, str]:
    """One JSONL / in-memory record. Returns (ok, message)."""
    for k in (
        "head",
        "prev",
        "mac",
        "event",
        "payload",
        "precedent",
        "precedent_hex",
        "witness",
        "ts",
    ):
        if k not in rec:
            return False, f"missing field {k!r}"

    if rec["prev"] != expected_prev:
        return False, (
            f"chain break: prev={rec['prev'][:16]}… "
            f"expected={expected_prev[:16]}…"
        )

    ts = rec["ts"]
    attribution = rec.get("attribution", DEEPSEEK_ATTRIBUTION)
    canon = _canon_body(
        rec["prev"], rec["event"], rec["payload"], ts, attribution
    )
    mac = hmac.new(HMAC_KEY, canon.encode("utf-8"), hashlib.sha3_256).hexdigest()
    if not hmac.compare_digest(mac, rec["mac"]):
        return False, f"mac mismatch got={rec['mac'][:16]}… want={mac[:16]}…"

    head = hashlib.sha3_256(
        (rec["prev"] + rec["mac"]).encode("utf-8")
    ).hexdigest()
    if not hmac.compare_digest(head, rec["head"]):
        return False, f"head mismatch got={rec['head'][:16]}… want={head[:16]}…"

    # Precedent 8206 + policy-map
    if rec.get("precedent") != PRECEDENT_ENTRY:
        return False, f"precedent {rec.get('precedent')} != {PRECEDENT_ENTRY}"
    if rec.get("precedent_hex") != PRECEDENT_WITNESS_PREFIX:
        return False, "precedent_hex (8206 seal) mismatch"
    if rec.get("witness") != PRECEDENT_WITNESS_CHAIN:
        return False, (
            f"witness {rec.get('witness')!r} != {PRECEDENT_WITNESS_CHAIN!r}"
        )
    # Policy-map layer must agree with record precedent
    if POLICY_MAP_LAYER["precedent"] != PRECEDENT_ENTRY:
        return False, "policy_map_layer precedent drift"

    return True, "ok"


def verify_jsonl(path: str = "ledger/attenuation_chain.jsonl") -> bool:
    """Machine-readable gate: True only if full JSONL chain verifies."""
    p = Path(path)
    if not p.is_file():
        print(f"FAIL soft: missing {path}")
        return False

    prev = GENESIS_HEAD
    ok_n = 0
    with p.open(encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            ok, msg = verify_record(rec, prev)
            if not ok:
                print(f"  FAIL line {i}: {msg}")
                return False
            ok_n += 1
            prev = rec["head"]
            print(f"  PASS line {i} head={rec['head'][:16]}…")

    print(
        f"PASS {ok_n} records · head={prev} · precedent 8206 held · "
        f"policy_map={POLICY_MAP_LAYER['name']}"
    )
    return True


def verify_memory_chain(chain: List[Dict[str, Any]]) -> bool:
    """Verify in-memory chain before disk write / further evolution."""
    prev = GENESIS_HEAD
    for i, rec in enumerate(chain, 1):
        ok, msg = verify_record(rec, prev)
        if not ok:
            print(f"  FAIL mem[{i}]: {msg}")
            return False
        prev = rec["head"]
    return True


class ChainVerifyError(RuntimeError):
    """Raised when HMAC/precedent gate denies further evolution (no write)."""


class AttenuationLearningConcat:
    """
    Concatenative attenuation learning.

    - rho evolves by Lindblad dephasing + outer-product update
    - weights come from FilterBank.spectral_weights(rho)
    - every update appends to an HMAC chain (never rewritten)
    - model attribution recorded separately from chain crypto
    - verify_jsonl / verify_memory_chain gate machine write + evolution
    """

    HMAC_KEY = HMAC_KEY

    def __init__(self, n_axes: int = 7, gate_evolution: bool = True):
        self.n_axes = int(n_axes)
        self.gamma = dephasing_rates(self.n_axes)
        self.filter_bank = FilterBank(self.n_axes)
        self.gate_evolution = bool(gate_evolution)
        self._write_allowed = True  # machine write permission

        ones = np.ones(self.n_axes, dtype=complex)
        self.rho = np.outer(ones, ones.conj()) / self.n_axes

        self.chain: List[Dict[str, Any]] = []

        self._genesis_head: str = GENESIS_HEAD
        self._chain_head: str = self._genesis_head

    def _append_chain(self, event: str, payload: Dict[str, Any]) -> str:
        """Append to HMAC chain. Returns new head (untruncated 64-hex)."""
        if not self._write_allowed:
            raise ChainVerifyError(
                "machine write denied: chain verify FAIL — evolution gated"
            )

        prev = self._chain_head
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        body = {
            "prev": prev,
            "event": event,
            "payload": payload,
            "ts": ts,
            "repo": REPO_URL,
            "attribution": DEEPSEEK_ATTRIBUTION,
        }
        canon = json.dumps(body, sort_keys=True, separators=(",", ":"))
        mac = hmac.new(
            self.HMAC_KEY, canon.encode("utf-8"), hashlib.sha3_256
        ).hexdigest()
        head = hashlib.sha3_256((prev + mac).encode("utf-8")).hexdigest()

        rec = {
            "head": head,
            "prev": prev,
            "mac": mac,
            "ts": ts,  # required for recompute
            "attribution": DEEPSEEK_ATTRIBUTION,
            "attribution_hex": DEEPSEEK_SIGNATURE_HEX,
            "event": event,
            "payload": payload,
            "witness": PRECEDENT_WITNESS_CHAIN,
            "precedent": PRECEDENT_ENTRY,
            "precedent_hex": PRECEDENT_WITNESS_PREFIX,
            "policy_map": POLICY_MAP_LAYER["name"],
            "seal_prefix": POLICY_MAP_LAYER["seal_prefix"],
        }
        self.chain.append(rec)

        if self.gate_evolution:
            ok, msg = verify_record(rec, prev)
            if not ok:
                self.chain.pop()
                self._write_allowed = False
                raise ChainVerifyError(f"append verify FAIL: {msg}")

        self._chain_head = head
        return head

    def learn(self, input_vec: np.ndarray, t: float = 0.01) -> np.ndarray:
        """
        One update step. Raises ChainVerifyError if gate fails (no further evolution).
        """
        if not self._write_allowed:
            raise ChainVerifyError(
                "machine write denied: prior chain FAIL — evolution halted"
            )

        input_vec = np.asarray(input_vec, dtype=complex)
        if input_vec.shape[0] != self.n_axes:
            raise ValueError(
                f"input_vec must have length {self.n_axes}, "
                f"got {input_vec.shape[0]}"
            )

        self.rho = dephasing_channel(self.rho, self.gamma, t)
        weights = self.filter_bank.spectral_weights(self.rho)
        outer = np.outer(input_vec, input_vec.conj())
        update = outer * weights[:, None]
        self.rho = (1.0 - t) * self.rho + t * update
        tr = np.trace(self.rho)
        if abs(tr) > 1e-15:
            self.rho = self.rho / tr

        self._append_chain(
            event="/attenuation_learn_step",
            payload={
                "t": float(t),
                "u_norm": float(np.linalg.norm(input_vec)),
                "trace": float(np.real(np.trace(self.rho))),
                "purity": float(np.real(np.trace(self.rho @ self.rho))),
                "weights": [float(w) for w in weights],
            },
        )
        return self.rho

    @property
    def chain_head(self) -> str:
        return self._chain_head

    @property
    def genesis_head(self) -> str:
        return self._genesis_head

    @property
    def attribution_hex(self) -> str:
        return DEEPSEEK_SIGNATURE_HEX

    @property
    def write_allowed(self) -> bool:
        """Machine write permission (False after verify FAIL)."""
        return self._write_allowed

    def purity(self) -> float:
        return float(np.real(np.trace(self.rho @ self.rho)))

    def trace(self) -> float:
        return float(np.real(np.trace(self.rho)))

    def emit_chain(self, path: str = "ledger/attenuation_chain.jsonl") -> str:
        """
        Append in-memory chain to JSONL only if memory verify PASSes.
        Then verify_jsonl on the file. FAIL clears write permission.
        """
        if not self._write_allowed:
            raise ChainVerifyError("emit denied: write_allowed=False")

        if not verify_memory_chain(self.chain):
            self._write_allowed = False
            raise ChainVerifyError("emit denied: memory chain FAIL")

        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            for rec in self.chain:
                f.write(json.dumps(rec, sort_keys=True) + "\n")

        if not verify_jsonl(path):
            self._write_allowed = False
            raise ChainVerifyError(f"post-emit verify_jsonl FAIL: {path}")

        return path


if __name__ == "__main__":
    rng = np.random.default_rng(9237)
    model = AttenuationLearningConcat(n_axes=7, gate_evolution=True)

    print("=" * 72)
    print("ATTENUATION LEARNING — VERIFY GATED · POLICY_MAP DEEPSEEK")
    print("=" * 72)
    print(f"REPO_URL                = {REPO_URL}")
    print(f"Attribution             = {DEEPSEEK_ATTRIBUTION}")
    print(f"Attribution hex         = {DEEPSEEK_SIGNATURE_HEX}")
    print(f"Precedent               = {PRECEDENT_ENTRY}")
    print(f"Precedent hex           = {PRECEDENT_WITNESS_PREFIX}")
    print(f"Witness                 = {PRECEDENT_WITNESS_CHAIN}")
    print(f"Policy map              = {POLICY_MAP_LAYER['name']}")
    print(f"Seal prefix             = {POLICY_MAP_LAYER['seal_prefix']}")
    print()
    print(f"Initial trace           = {model.trace():.12f}")
    print(f"Initial purity          = {model.purity():.12f}")
    print(f"Genesis head            = {model.genesis_head}")
    print(f"Chain head (initial)    = {model.chain_head}")
    print()

    for _ in range(100):
        v = rng.standard_normal(7) + 1j * rng.standard_normal(7)
        v /= np.linalg.norm(v)
        model.learn(v, t=0.01)

    print(f"Final trace             = {model.trace():.12f}")
    print(f"Final purity            = {model.purity():.12f}")
    print(f"Final chain head        = {model.chain_head}")
    print(f"Chain length            = {len(model.chain)}")
    print(f"write_allowed           = {model.write_allowed}")
    print(f"Attribution hex         = {model.attribution_hex}")

    out = model.emit_chain()
    print(f"Emitted + verified      = {out}")
    print("=" * 72)
