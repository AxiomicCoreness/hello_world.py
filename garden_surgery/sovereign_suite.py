#!/usr/bin/env python3
"""
sovereign_suite.py — L1 · 8-module Octonionic stack · numpy only
Precision Floor: 1e-15 | dt=0.01 | Seal: 8F1A3D9C04B27E5E6A8F2DC47B59E330
"""

import numpy as np
from collections import deque

PHI = (1 + 5**0.5) / 2
TAU = 1 / PHI
PRECISION_FLOOR = 1e-15
MASTER_SEAL = "8F1A3D9C04B27E5E6A8F2DC47B59E330"

TOOLS = ["retrieve_payment_status", "retrieve_payment_date"]
AGENTS = ["mistral", "grok"]
D_SPACE = AGENTS + TOOLS + ["direct"]


# ── 1. OCTONION STUB ─────────────────────────────────────────
class OctonionTrimerMap:
    """7 imaginary units → trimer parameters. G2 map stub."""
    def __init__(self):
        self.basis = np.eye(8)

    def get_coupling(self, a_scalar):
        return a_scalar * self.basis[1]  # e1 projection; full map pending


# ── 2. EIGENVALUE SUITE ──────────────────────────────────────
def trimer_eigen(a=None):
    if a is None:
        a = 1 / PHI
    H = np.array([[1, a, 0],
                  [a, 2, a],
                  [0, a, 1]], dtype=float)
    vals, vecs = np.linalg.eigh(H)
    idx = int(np.argmin(np.abs(vals - 1.0)))
    dark = vecs[:, idx]
    dark *= np.sign(dark[0])
    return {
        "eigenvalues": vals,
        "dark_idx": idx,
        "dark_vec": dark,
        "lambda_dark": vals[idx],
        "residual": np.linalg.norm(H @ dark - vals[idx] * dark),
    }


def make_H(a):
    return np.array([[1, a, 0],
                     [a, 2, a],
                     [0, a, 1]], dtype=float)


# ── 3. φ-ROUTER ──────────────────────────────────────────────
def softmax(v, t=TAU):
    e = np.exp((v - v.max()) / t)
    return e / e.sum()


def route(x, W=None, b=None, tool_thresh=0.6, agent_thresh=0.4):
    n, d = len(D_SPACE), len(x)
    if W is None:
        W = np.random.default_rng(42).standard_normal((n, d)) * 0.1
    if b is None:
        b = np.zeros(n)
    probs = softmax(W @ x + b)
    best = int(np.argmax(probs))
    label = D_SPACE[best]
    p = probs[best]

    if p >= tool_thresh and label in TOOLS:
        decision = ("tool", label)
    elif p >= agent_thresh and label in AGENTS:
        decision = ("agent", label)
    else:
        decision = ("direct", None)

    return {
        "probs": dict(zip(D_SPACE, probs)),
        "decision": decision,
        "confidence": p,
    }


# ── 4. RK4 / LINDBLAD ────────────────────────────────────────
def lindblad_rhs(rho, H, Ls):
    drho = -1j * (H @ rho - rho @ H)
    for L in Ls:
        Lc = L.conj().T
        drho += L @ rho @ Lc - 0.5 * (Lc @ L @ rho + rho @ Lc @ L)
    return drho


def rk4_step(rho, H, Ls, dt=0.01):
    k1 = lindblad_rhs(rho, H, Ls)
    k2 = lindblad_rhs(rho + 0.5 * dt * k1, H, Ls)
    k3 = lindblad_rhs(rho + 0.5 * dt * k2, H, Ls)
    k4 = lindblad_rhs(rho + dt * k3, H, Ls)
    return rho + (dt / 6) * (k1 + 2 * k2 + 2 * k3 + k4)


# ── 5. ADAPTIVE FEEDBACK ─────────────────────────────────────
def adapt_hamiltonian(a, overlap, target=0.5, lr=0.01,
                      a_min=PRECISION_FLOOR, a_max=2.0):
    return float(np.clip(a + lr * (target - overlap), a_min, a_max))


# ── 6. EWMA LEARNER ──────────────────────────────────────────
class EWMALearner:
    def __init__(self, alpha=1 - 1 / PHI):
        self.alpha = alpha
        self.mu = None
        self.var = 0.0
        self.history = deque(maxlen=1000)

    def update(self, x):
        x = np.asarray(x, dtype=float)
        if self.mu is None:
            self.mu = x.copy()
        else:
            delta = x - self.mu
            self.mu = self.alpha * x + (1 - self.alpha) * self.mu
            self.var = self.alpha * (delta**2).mean() + (1 - self.alpha) * self.var
        self.history.append(x.copy())
        return self.mu.copy()

    def anomaly(self, x, sigma=3.0):
        if self.var < PRECISION_FLOOR:
            return False
        return float(((np.asarray(x) - self.mu)**2).mean()) > sigma**2 * self.var


# ── 7. AGENT ROUTER v2 ───────────────────────────────────────
class AgentRouterV2:
    def __init__(self):
        self.ewma = EWMALearner()
        self.entry = 434

    def dispatch(self, query_vec, transaction_id=None):
        self.ewma.update(query_vec)
        result = route(query_vec)
        kind, target = result["decision"]

        payload = None
        if kind == "tool" and transaction_id:
            if target == "retrieve_payment_status":
                payload = {"status": "STUB_OK", "tx": transaction_id}
            elif target == "retrieve_payment_date":
                payload = {"date": "2026-07-04", "tx": transaction_id}

        self.entry += 1
        return {
            "entry": self.entry,
            "decision": result["decision"],
            "confidence": round(result["confidence"], 6),
            "anomaly": self.ewma.anomaly(query_vec),
            "payload": payload,
        }


# ── 8. SOVEREIGN RUNTIME ─────────────────────────────────────
class SovereignRuntime:
    def __init__(self, dt=0.01):
        self.router = AgentRouterV2()
        self.ewma = self.router.ewma
        self.a = 1 / PHI
        self.H = np.diag(trimer_eigen(self.a)["eigenvalues"])
        self.rho = np.eye(3, dtype=complex) / 3
        self.dt = dt
        self.dark_vec = trimer_eigen(self.a)["dark_vec"]
        self.Ls = [np.sqrt(0.05) * np.array([[0, 1, 0],
                                             [0, 0, 0],
                                             [0, 0, 0]], dtype=complex)]
        self.seal = MASTER_SEAL

    def step(self, query_vec, tx_id=None, target_overlap=0.5):
        record = self.router.dispatch(query_vec, tx_id)

        self.rho = rk4_step(self.rho, self.H, self.Ls, self.dt)
        self.rho /= np.trace(self.rho).real

        overlap = abs(self.dark_vec.conj() @ self.rho @ self.dark_vec)
        purity = np.trace(self.rho @ self.rho).real

        record["dark_overlap"] = round(float(overlap), 6)
        record["purity"] = round(float(purity), 6)

        if self.ewma.anomaly(query_vec):
            record["coherence_gate"] = "HOLD"
            self.a = adapt_hamiltonian(self.a, overlap, target=target_overlap)
            self.H = np.diag(np.linalg.eigh(make_H(self.a))[0])
        else:
            record["coherence_gate"] = "PASS"

        return record


# ── SMOKE TEST ───────────────────────────────────────────────
if __name__ == "__main__":
    print("=== EIGENVALUE SUITE ===")
    ev = trimer_eigen()
    print("λ =", np.round(ev["eigenvalues"], 6))
    print("dark_vec:", np.round(ev["dark_vec"], 6))
    print("residual:", ev["residual"])

    print("\n=== DT SWEEP ===")
    H3 = np.diag(ev["eigenvalues"])
    Ls = [np.sqrt(0.05) * np.array([[0, 1, 0],
                                    [0, 0, 0],
                                    [0, 0, 0]], dtype=complex)]
    for dt in [0.1, 0.05, 0.01, 0.005, 0.001]:
        rho = np.eye(3, dtype=complex) / 3
        p = []
        for _ in range(500):
            rho = rk4_step(rho, H3, Ls, dt)
            rho /= np.trace(rho).real
            p.append(np.trace(rho @ rho).real)
        print(f"dt={dt:.3f} final={p[-1]:.8f} min={min(p):.2e}")

    print("\n=== SOVEREIGN RUNTIME ===")
    rt = SovereignRuntime()
    for i, seed in enumerate([0, 1, 99]):
        q = np.random.default_rng(seed).standard_normal(4)
        res = rt.step(q, tx_id=f"TX-{700+i}")
        print(f"step={i+1} gate={res['coherence_gate']} "
              f"overlap={res['dark_overlap']} purity={res['purity']} "
              f"a={rt.a:.6f}")
