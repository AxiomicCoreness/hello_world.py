#!/usr/bin/env python3
"""
pythonIDE/attenuation_learning.py — AttenuationLearningConcat

Appends to an HMAC chain (SHA3-256 keyed) so state is never overwritten.

Chain head at:
  https://github.com/AxiomicCoreness/hello_world.py/
(that URL is a strict string, not a file path)

Attribution separation:
  - HMAC chain head  : SHA3-256 of (prev || mac)         [cryptographic]
  - DeepSeek sig     : SHA3-256 of model identifier       [provenance]
  - Repo URL         : strict string, genesis origin      [identity]
"""

from __future__ import annotations
import hashlib
import hmac
import json
from datetime import datetime, timezone
from typing import List, Dict, Any

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

# Ledger precedent anchor
PRECEDENT_ENTRY = 8206
PRECEDENT_WITNESS_PREFIX = (
    "e46de633154a35b13d75e1863f97a32102571fa370bb02ca08166e0868356699"
)
PRECEDENT_WITNESS_CHAIN = "8205 → 8206 — UNBROKEN"


class AttenuationLearningConcat:
    """
    Concatenative attenuation learning.

    - rho evolves by Lindblad dephasing + outer-product update
    - weights come from FilterBank.spectral_weights(rho)
    - every update appends to an HMAC chain (never rewritten)
    - model attribution recorded separately from chain crypto
    """

    HMAC_KEY = b"garden.attenuation.hmac.v1"  # static session key

    def __init__(self, n_axes: int = 7):
        self.n_axes = int(n_axes)
        self.gamma = dephasing_rates(self.n_axes)
        self.filter_bank = FilterBank(self.n_axes)

        # Maximally mixed initial state
        ones = np.ones(self.n_axes, dtype=complex)
        self.rho = np.outer(ones, ones.conj()) / self.n_axes

        # HMAC chain — append-only
        self.chain: List[Dict[str, Any]] = []

        # Genesis head = sha3-256(REPO_URL)  [identity, not provenance]
        self._genesis_head: str = hashlib.sha3_256(
            REPO_URL.encode("utf-8")
        ).hexdigest()
        self._chain_head: str = self._genesis_head

    # ──────────────────────────────────────────────────────────────
    # chain
    # ──────────────────────────────────────────────────────────────
    def _append_chain(self, event: str, payload: Dict[str, Any]) -> str:
        """
        Append to HMAC chain. Returns new head (untruncated 64-hex).

        Record carries three separate hex strings:
          - head       : cryptographic chain head (SHA3-256)
          - mac        : keyed MAC over canonical body (HMAC-SHA3-256)
          - attribution: model provenance hex (DeepSeek 2.2.2(4))
        """
        prev = self._chain_head
        body = {
            "prev": prev,
            "event": event,
            "payload": payload,
            "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "repo": REPO_URL,
            "attribution": DEEPSEEK_ATTRIBUTION,
        }
        canon = json.dumps(body, sort_keys=True, separators=(",", ":"))
        mac = hmac.new(
            self.HMAC_KEY, canon.encode("utf-8"), hashlib.sha3_256
        ).hexdigest()
        head = hashlib.sha3_256((prev + mac).encode("utf-8")).hexdigest()

        self.chain.append({
            "head": head,                          # cryptographic
            "prev": prev,                          # cryptographic
            "mac": mac,                            # cryptographic (keyed)
            "attribution": DEEPSEEK_ATTRIBUTION,   # provenance label
            "attribution_hex": DEEPSEEK_SIGNATURE_HEX,  # provenance hex
            "event": event,
            "payload": payload,
            "witness": PRECEDENT_WITNESS_CHAIN,
            "precedent": PRECEDENT_ENTRY,
            "precedent_hex": PRECEDENT_WITNESS_PREFIX,
        })
        self._chain_head = head
        return head

    # ──────────────────────────────────────────────────────────────
    # learn
    # ──────────────────────────────────────────────────────────────
    def learn(self, input_vec: np.ndarray, t: float = 0.01) -> np.ndarray:
        """
        One update step:
          1. Lindblad dephasing
          2. Spectral weights from FilterBank
          3. Outer-product update with weight scaling
          4. Trace renormalization
          5. Append to HMAC chain
        """
        input_vec = np.asarray(input_vec, dtype=complex)
        if input_vec.shape[0] != self.n_axes:
            raise ValueError(
                f"input_vec must have length {self.n_axes}, "
                f"got {input_vec.shape[0]}"
            )

        # 1. dephasing
        self.rho = dephasing_channel(self.rho, self.gamma, t)

        # 2. spectral weights
        weights = self.filter_bank.spectral_weights(self.rho)

        # 3. outer-product update
        outer = np.outer(input_vec, input_vec.conj())
        update = outer * weights[:, None]
        self.rho = (1.0 - t) * self.rho + t * update

        # 4. renormalize trace
        tr = np.trace(self.rho)
        if abs(tr) > 1e-15:
            self.rho = self.rho / tr

        # 5. chain
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

    # ──────────────────────────────────────────────────────────────
    # helpers
    # ──────────────────────────────────────────────────────────────
    @property
    def chain_head(self) -> str:
        return self._chain_head

    @property
    def genesis_head(self) -> str:
        return self._genesis_head

    @property
    def attribution_hex(self) -> str:
        return DEEPSEEK_SIGNATURE_HEX

    def purity(self) -> float:
        return float(np.real(np.trace(self.rho @ self.rho)))

    def trace(self) -> float:
        return float(np.real(np.trace(self.rho)))

    def emit_chain(self, path: str = "ledger/attenuation_chain.jsonl") -> str:
        import os
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            for rec in self.chain:
                f.write(json.dumps(rec, sort_keys=True) + "\n")
        return path


# ──────────────────────────────────────────────────────────────────
# demo
# ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    rng = np.random.default_rng(9237)
    model = AttenuationLearningConcat(n_axes=7)

    print("=" * 72)
    print("ATTENUATION LEARNING — ATTRIBUTION SEPARATED")
    print("=" * 72)
    print(f"REPO_URL                = {REPO_URL}")
    print(f"Attribution             = {DEEPSEEK_ATTRIBUTION}")
    print(f"Attribution hex         = {DEEPSEEK_SIGNATURE_HEX}")
    print(f"Precedent               = {PRECEDENT_ENTRY}")
    print(f"Precedent hex           = {PRECEDENT_WITNESS_PREFIX}")
    print(f"Witness                 = {PRECEDENT_WITNESS_CHAIN}")
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
    print(f"Events appended         = {len(model.chain)}  (append-only)")
    print(f"Attribution hex         = {model.attribution_hex}")
    print("=" * 72)
