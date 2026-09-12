#!/usr/bin/env python3
"""
pythonIDE/attenuation_learning.py — AttenuationLearningConcat

Appends to an HMAC chain (SHA3-256 keyed) so state is never overwritten.
Every emit is followed by verify_jsonl / verify_memory_chain; FAIL gates
further evolution (machine write permission denied).

Policy-map layer (DeepSeek tab) cites precedent 8206 + φ frame.
"""

from __future__ import annotations
import hashlib
import hmac
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Tuple

import numpy as np

from pythonIDE.dephasing import dephasing_rates, dephasing_channel
from pythonIDE.axes import FilterBank

PHI = (1.0 + np.sqrt(5.0)) / 2.0
REPO_URL = "https://github.com/AxiomicCoreness/hello_world.py/"
DEEPSEEK_ATTRIBUTION = "DeepSeek 2.2.2(4)"
DEEPSEEK_SIGNATURE_HEX = hashlib.sha3_256(
    DEEPSEEK_ATTRIBUTION.encode("utf-8")
).hexdigest()
PRECEDENT_ENTRY = 8206
PRECEDENT_WITNESS_PREFIX = (
    "e46de633154a35b13d75e1863f97a32102571fa370bb02ca08166e0868356699"
)
PRECEDENT_WITNESS_CHAIN = "8205 → 8206 — UNBROKEN"
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


def _canon_body(prev, event, payload, ts, attribution):
    body = {
        "prev": prev,
        "event": event,
        "payload": payload,
        "ts": ts,
        "repo": REPO_URL,
        "attribution": attribution,
    }
    return json.dumps(body, sort_keys=True, separators=(",", ":"))


def verify_record(rec, expected_prev):
    for k in ("head", "prev", "mac", "event", "payload", "precedent",
              "precedent_hex", "witness", "ts"):
        if k not in rec:
            return False, f"missing field {k!r}"
    if rec["prev"] != expected_prev:
        return False, f"chain break: prev={rec['prev'][:16]}…"
    attribution = rec.get("attribution", DEEPSEEK_ATTRIBUTION)
    canon = _canon_body(rec["prev"], rec["event"], rec["payload"],
                        rec["ts"], attribution)
    mac = hmac.new(HMAC_KEY, canon.encode("utf-8"), hashlib.sha3_256).hexdigest()
    if not hmac.compare_digest(mac, rec["mac"]):
        return False, "mac mismatch"
    head = hashlib.sha3_256((rec["prev"] + rec["mac"]).encode("utf-8")).hexdigest()
    if not hmac.compare_digest(head, rec["head"]):
        return False, "head mismatch"
    if rec.get("precedent") != PRECEDENT_ENTRY:
        return False, "precedent mismatch"
    if rec.get("precedent_hex") != PRECEDENT_WITNESS_PREFIX:
        return False, "precedent_hex mismatch"
    if rec.get("witness") != PRECEDENT_WITNESS_CHAIN:
        return False, "witness mismatch"
    if POLICY_MAP_LAYER["precedent"] != PRECEDENT_ENTRY:
        return False, "policy_map_layer precedent drift"
    return True, "ok"


def verify_jsonl(path="ledger/attenuation_chain.jsonl"):
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
    print(f"PASS {ok_n} records · head={prev} · 8206 · {POLICY_MAP_LAYER['name']}")
    return True


def verify_memory_chain(chain):
    prev = GENESIS_HEAD
    for i, rec in enumerate(chain, 1):
        ok, msg = verify_record(rec, prev)
        if not ok:
            print(f"  FAIL mem[{i}]: {msg}")
            return False
        prev = rec["head"]
    return True


class ChainVerifyError(RuntimeError):
    pass


class AttenuationLearningConcat:
    HMAC_KEY = HMAC_KEY

    def __init__(self, n_axes=7, gate_evolution=True):
        self.n_axes = int(n_axes)
        self.gamma = dephasing_rates(self.n_axes)
        self.filter_bank = FilterBank(self.n_axes)
        self.gate_evolution = bool(gate_evolution)
        self._write_allowed = True
        ones = np.ones(self.n_axes, dtype=complex)
        self.rho = np.outer(ones, ones.conj()) / self.n_axes
        self.chain = []
        self._genesis_head = GENESIS_HEAD
        self._chain_head = self._genesis_head

    def _append_chain(self, event, payload):
        if not self._write_allowed:
            raise ChainVerifyError("machine write denied: chain verify FAIL")
        prev = self._chain_head
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        body = {
            "prev": prev, "event": event, "payload": payload,
            "ts": ts, "repo": REPO_URL, "attribution": DEEPSEEK_ATTRIBUTION,
        }
        canon = json.dumps(body, sort_keys=True, separators=(",", ":"))
        mac = hmac.new(self.HMAC_KEY, canon.encode("utf-8"), hashlib.sha3_256).hexdigest()
        head = hashlib.sha3_256((prev + mac).encode("utf-8")).hexdigest()
        rec = {
            "head": head, "prev": prev, "mac": mac, "ts": ts,
            "attribution": DEEPSEEK_ATTRIBUTION,
            "attribution_hex": DEEPSEEK_SIGNATURE_HEX,
            "event": event, "payload": payload,
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

    def learn(self, input_vec, t=0.01):
        if not self._write_allowed:
            raise ChainVerifyError("machine write denied: evolution halted")
        input_vec = np.asarray(input_vec, dtype=complex)
        if input_vec.shape[0] != self.n_axes:
            raise ValueError(f"input_vec length {self.n_axes} required")
        self.rho = dephasing_channel(self.rho, self.gamma, t)
        weights = self.filter_bank.spectral_weights(self.rho)
        outer = np.outer(input_vec, input_vec.conj())
        self.rho = (1.0 - t) * self.rho + t * (outer * weights[:, None])
        tr = np.trace(self.rho)
        if abs(tr) > 1e-15:
            self.rho = self.rho / tr
        self._append_chain("/attenuation_learn_step", {
            "t": float(t),
            "u_norm": float(np.linalg.norm(input_vec)),
            "trace": float(np.real(np.trace(self.rho))),
            "purity": float(np.real(np.trace(self.rho @ self.rho))),
            "weights": [float(w) for w in weights],
        })
        return self.rho

    @property
    def chain_head(self):
        return self._chain_head

    @property
    def genesis_head(self):
        return self._genesis_head

    @property
    def attribution_hex(self):
        return DEEPSEEK_SIGNATURE_HEX

    @property
    def write_allowed(self):
        return self._write_allowed

    def purity(self):
        return float(np.real(np.trace(self.rho @ self.rho)))

    def trace(self):
        return float(np.real(np.trace(self.rho)))

    def emit_chain(self, path="ledger/attenuation_chain.jsonl"):
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
    for _ in range(100):
        v = rng.standard_normal(7) + 1j * rng.standard_normal(7)
        v /= np.linalg.norm(v)
        model.learn(v, t=0.01)
    print("head", model.chain_head)
    print("write_allowed", model.write_allowed)
    print("emitted", model.emit_chain())
