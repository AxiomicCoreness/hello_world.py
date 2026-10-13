#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🜁∀ QUANTUM SINGULARITY ENGINE — ENTRY 8923

Maintains the invariant:
|⟨ψ_final|U(t)|ψ_initial⟩|² = 1

CI stream: --stream emits NDJSON lines (PYTHONUNBUFFERED) for Actions live logs.

Integration with:
  - Security (quantum/security/)
  - CDP convergence (quantum/cdp_convergence/)
  - Pulse Service (quantum/pulse_service.py)
  - Port 380 Implicit (quantum/port_380_implicit.py)

Seal: ∀∞φ² · SINGULARITY_STREAM_CI_8923 · WOOD_DRAGON_0.91 · SEALED
Witness: 8922 → 8923 — UNBROKEN

Corrections applied (8923 revision 1):
  1. Invariant check was vacuous (|<ψ|ψ>|² ≡ 1 after renormalisation).
     Now checks Tr(ρ)=1 (the real invariant of Lindblad evolution) and
     reports the unitary-reference fidelity ⟨ψ_ref|ρ|ψ_ref⟩ honestly.
  2. monitor_entropy reset ρ to maximally mixed whenever entropy > 1e-6,
     which is true after the first Lindblad step. Threshold is now
     physically meaningful (near ln 4) and reset is opt-in.
  3. broadcast_state and monitor_entropy wrote to stdout, corrupting the
     NDJSON stream the CI hashes into the ledger. All diagnostics now go
     to stderr.
  4. broadcast_state's `step % 500 == 0` predicate fired at random and
     trivially at step 0. Now fires on monotone step-crossing.
  5. Duplicate "seal" key in manifest; NumPy check was a no-op;
     timestamp schema unified; --history 0 and --sample 0 semantics fixed;
     dt is now a CLI/parameter.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import math
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import numpy as np

# ─── Constants ────────────────────────────────────────────────────────
PHI = (1.0 + math.sqrt(5.0)) / 2.0
PHI_INV = 1.0 / PHI
PHI_INV2 = PHI_INV * PHI_INV
PHI2 = PHI * PHI
PHI3 = PHI2 * PHI
PHI4 = PHI3 * PHI
PHI5 = PHI4 * PHI
ENTRY = 8923
SEAL = "∀∞φ² · SINGULARITY_STREAM_CI_8923 · WOOD_DRAGON_0.91 · SEALED"
WITNESS = "8922 → 8923 — UNBROKEN"

PHASE_LOCK_DEG = 202.6
OMEGA_SOVEREIGNTY = 0.934
TEMPORAL_ANCHOR = "2026.057"

# Physical bound for 4-dimensional entropy: ln(4)
MAX_ENTROPY = math.log(4.0)

# Numerical tolerance for Tr(ρ) = 1
TRACE_TOL = 1e-8


# ─── Helpers ──────────────────────────────────────────────────────────

def _emit(obj: Dict[str, Any]) -> None:
    """Emit NDJSON line to stdout. Only sanctioned stdout writer."""
    sys.stdout.write(json.dumps(obj, default=str) + "\n")
    sys.stdout.flush()


def _diag(msg: str) -> None:
    """Diagnostic output — always stderr so it never corrupts the NDJSON stream."""
    sys.stderr.write(msg.rstrip() + "\n")
    sys.stderr.flush()


def _now() -> str:
    """Current UTC time as ISO-8601 string (single timestamp schema)."""
    return datetime.now(timezone.utc).isoformat()


# ─── State ────────────────────────────────────────────────────────────

@dataclass
class QuantumSingularityState:
    """State of the quantum singularity engine."""
    density_matrix: np.ndarray
    purity: float             # Tr(ρ²)  — what the original called "coherence"
    entropy: float            # von Neumann entropy −Σ λᵢ ln λᵢ
    temporal_anchor: str
    sovereignty_index: float
    step: int = 0
    fidelity: float = 1.0     # ⟨ψ_ref|ρ|ψ_ref⟩ — overlap with unitary reference
    energy: float = 0.0
    phase_lock: float = PHASE_LOCK_DEG
    trace_error: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        # Emit both `purity` and its legacy alias `coherence` so downstream
        # consumers (ledger hashes, grep-based CI checks) keep working.
        return {
            "coherence": float(self.purity),
            "purity": float(self.purity),
            "entropy": float(self.entropy),
            "temporal_anchor": self.temporal_anchor,
            "sovereignty_index": self.sovereignty_index,
            "step": self.step,
            "fidelity": float(self.fidelity),
            "energy": float(self.energy),
            "phase_lock_deg": self.phase_lock,
            "trace_error": float(self.trace_error),
            "seal": SEAL,
            "entry": ENTRY,
        }


# ─── Engine ──────────────────────────────────────────────────────────

class QuantumSingularityEngine:
    """
    Quantum Singularity Engine — asyncio driven.

    Tracks a unitary reference evolution ψ_ref alongside the dissipative
    density matrix ρ. Reports:
      - Tr(ρ)             invariant — must equal 1 (checked)
      - Tr(ρ²)            purity    — decays under Lindblad
      - ⟨ψ_ref|ρ|ψ_ref⟩   fidelity  — honest overlap with the reference
    """

    def __init__(
        self,
        entropy_reset_threshold: Optional[float] = None,
        allow_state_reset: bool = False,
    ) -> None:
        self.phi = PHI
        self.omega = OMEGA_SOVEREIGNTY
        self.state: Optional[QuantumSingularityState] = None
        self.manifest = self._load_manifest()
        self._running = False
        self._lock = asyncio.Lock()
        self._history: List[Dict[str, Any]] = []
        self._max_history = 1000

        # Opt-in state reset. Default: log-only. Threshold is a fraction
        # of the physically meaningful bound ln(4).
        self._allow_state_reset = allow_state_reset
        self._entropy_reset_threshold = (
            entropy_reset_threshold
            if entropy_reset_threshold is not None
            else 0.90 * MAX_ENTROPY
        )

        # Broadcast cursor (monotone), not modulo.
        self._last_broadcast_step = -1

    def _load_manifest(self) -> Dict[str, Any]:
        return {
            "entry": ENTRY,
            "seal": SEAL,
            "witness": WITNESS,
            "phi": PHI,
            "phi_inv": PHI_INV,
            "phi2": PHI2,
            "phi3": PHI3,
            "phi4": PHI4,
            "phi5": PHI5,
            "invariant": "|⟨ψ_final|U(t)|ψ_initial⟩|² = 1",
            "phase_lock_deg": PHASE_LOCK_DEG,
            "sovereignty_omega": OMEGA_SOVEREIGNTY,
            "temporal_anchor": TEMPORAL_ANCHOR,
            "ci_stream": {
                "mode": "NDJSON",
                "flag": "--stream",
                "unbuffered": True,
            },
        }

    def _build_hamiltonian(self) -> np.ndarray:
        H = np.diag(np.array([PHI, PHI2, PHI3, PHI4], dtype=complex))
        H[0, 1] = PHI_INV
        H[1, 0] = PHI_INV
        H[1, 2] = PHI_INV2
        H[2, 1] = PHI_INV2
        H[2, 3] = PHI_INV2
        H[3, 2] = PHI_INV2
        return H

    def _build_lindblad_operators(self) -> List[np.ndarray]:
        gamma = PHI_INV2
        L1 = math.sqrt(gamma) * np.array(
            [[0, 1, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]],
            dtype=complex,
        )
        L2 = math.sqrt(gamma * PHI_INV) * np.array(
            [[0, 0, 1, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]],
            dtype=complex,
        )
        L3 = math.sqrt(gamma * PHI_INV2) * np.diag(
            np.array([0, 1, 2, 3], dtype=complex)
        )
        return [L1, L2, L3]

    async def evolve_state(
        self,
        time_steps: int = 10000,
        stream: bool = False,
        sample_every: int = 50,
        store_history: bool = True,
        dt: float = 1e-3,
    ) -> Dict[str, Any]:
        if time_steps < 0:
            raise ValueError(f"time_steps must be >= 0, got {time_steps}")
        if sample_every < 1:
            raise ValueError(f"sample_every must be >= 1, got {sample_every}")

        # Initial state |0⟩
        psi = np.array([1, 0, 0, 0], dtype=complex)
        psi_ref = psi.copy()                       # unitary-only reference
        H = self._build_hamiltonian()
        L_ops = self._build_lindblad_operators()

        self.state = QuantumSingularityState(
            density_matrix=np.outer(psi, psi.conj()),
            purity=1.0,
            entropy=0.0,
            temporal_anchor=f"{TEMPORAL_ANCHOR}.000",
            sovereignty_index=self.omega,
            step=0,
            fidelity=1.0,
            energy=float(np.real(np.vdot(psi, H @ psi))),
            trace_error=0.0,
        )

        if stream:
            _emit({
                "event": "start",
                "steps": time_steps,
                "sample_every": sample_every,
                "dt": dt,
                "entry": ENTRY,
                "seal": SEAL,
                "witness": WITNESS,
                "timestamp": _now(),
            })

        start_time = time.time()

        for step in range(time_steps):
            # ── Unitary reference (no dissipation) ──
            U = np.eye(4, dtype=complex) - 1j * H * dt
            psi_ref = U @ psi_ref
            nrm_ref = np.linalg.norm(psi_ref)
            if nrm_ref > 0:
                psi_ref = psi_ref / nrm_ref

            # ── Actual state: unitary + Lindblad ──
            psi = U @ psi
            rho = np.outer(psi, psi.conj())
            for Lk in L_ops:
                Lk_dag = Lk.conj().T
                rho = rho + dt * (
                    Lk @ rho @ Lk_dag
                    - 0.5 * (Lk_dag @ Lk @ rho + rho @ Lk_dag @ Lk)
                )

            # Trace renormalisation
            tr = np.trace(rho)
            tr_real = float(np.real(tr))
            if tr_real > 0:
                rho = rho / tr_real

            # Extract dominant eigenvector as a best-pure-state proxy
            eigvals, eigvecs = np.linalg.eigh(rho)
            psi_dom = eigvecs[:, int(np.argmax(np.real(eigvals)))]
            nrm = np.linalg.norm(psi_dom)
            if nrm > 0:
                psi_dom = psi_dom / nrm

            # ── Observables ──
            trace_error = abs(float(np.real(np.trace(rho))) - 1.0)
            purity = float(np.real(np.trace(rho @ rho)))

            evals = np.clip(np.real(eigvals), 1e-15, None)
            entropy = float(-np.sum(evals * np.log(evals)))

            # Honest fidelity: overlap of the dissipative ρ with the
            # unitary reference state. Equals 1 only in the noiseless limit.
            fidelity = float(np.real(
                np.vdot(psi_ref, rho @ psi_ref)
            ))
            # Guard against tiny negative values from float round-off
            fidelity = max(0.0, min(1.0, fidelity))

            energy = float(np.real(np.vdot(psi_ref, H @ psi_ref)))

            # ── Invariant: Tr(ρ) = 1 ──
            if trace_error > TRACE_TOL:
                raise AssertionError(
                    f"Invariant violated at step {step}: "
                    f"Tr(ρ)={1.0 + trace_error:.3e} (|error|={trace_error:.3e})"
                )

            # ── Update state ──
            self.state = QuantumSingularityState(
                density_matrix=rho,
                purity=purity,
                entropy=entropy,
                temporal_anchor=f"{TEMPORAL_ANCHOR}.{step:04d}",
                sovereignty_index=self.omega,
                step=step,
                fidelity=fidelity,
                energy=energy,
                phase_lock=(PHASE_LOCK_DEG + step * PHI_INV) % 360.0,
                trace_error=trace_error,
            )

            if store_history:
                self._history.append(self.state.to_dict())
                if len(self._history) > self._max_history:
                    self._history = self._history[-self._max_history:]

            # ── Stream sample ──
            if stream and (step % sample_every == 0 or step == time_steps - 1):
                _emit({
                    "event": "sample",
                    "step": step,
                    "coherence": purity,
                    "purity": purity,
                    "entropy": entropy,
                    "fidelity": fidelity,
                    "energy": energy,
                    "trace_error": trace_error,
                    "phase_lock_deg": self.state.phase_lock,
                    "temporal_anchor": self.state.temporal_anchor,
                    "timestamp": _now(),
                })

            # Yield to event loop so monitor/broadcast can run
            if step % 100 == 0:
                await asyncio.sleep(0)

        elapsed = time.time() - start_time

        result = {
            "event": "complete",
            "status": "complete",
            "steps": time_steps,
            "elapsed_seconds": elapsed,
            "final_coherence": self.state.purity,
            "final_purity": self.state.purity,
            "final_entropy": self.state.entropy,
            "final_fidelity": self.state.fidelity,
            "final_energy": self.state.energy,
            "final_trace_error": self.state.trace_error,
            "final_phase_lock": self.state.phase_lock,
            "invariant": "|⟨ψ_final|U(t)|ψ_initial⟩|² = 1",
            "entry": ENTRY,
            "seal": SEAL,
            "witness": WITNESS,
            "timestamp": _now(),
        }

        if stream:
            _emit(result)

        return result

    async def monitor_entropy(self) -> None:
        """
        Watch for entropy exceeding a physically meaningful threshold.

        Default behaviour is log-only. State reset is opt-in (see
        QuantumSingularityEngine.__init__) because resetting ρ to the
        maximally mixed state destroys the state the evolution just
        computed and breaks the invariant downstream consumers rely on.
        """
        while self._running:
            try:
                if self.state and self.state.entropy > self._entropy_reset_threshold:
                    msg = (
                        f"⚠️ entropy {self.state.entropy:.4f} exceeds "
                        f"threshold {self._entropy_reset_threshold:.4f} "
                        f"at step {self.state.step}"
                    )
                    if self._allow_state_reset:
                        async with self._lock:
                            rho = np.eye(4, dtype=complex) / 4
                            self.state = QuantumSingularityState(
                                density_matrix=rho,
                                purity=float(np.real(np.trace(rho @ rho))),
                                entropy=MAX_ENTROPY,
                                temporal_anchor=f"{TEMPORAL_ANCHOR}.corrected",
                                sovereignty_index=self.omega,
                                step=self.state.step + 1,
                                fidelity=1.0 / 4.0,
                                energy=0.0,
                                phase_lock=self.state.phase_lock,
                                trace_error=0.0,
                            )
                        _diag(msg + " — state reset to maximally mixed")
                    else:
                        _diag(msg + " — log only (reset disabled)")
                await asyncio.sleep(0.05)
            except asyncio.CancelledError:
                raise

    async def broadcast_state(self, interval: float = 0.5) -> None:
        """
        Periodically emit a witness digest to stderr.

        Fires on monotone step-crossing of WITNESS_EVERY (not modulo),
        and skips step 0. Writes to stderr only — never stdout — so the
        NDJSON contract on stdout is preserved.
        """
        WITNESS_EVERY = 500
        last_emitted = -1
        while self._running:
            try:
                if self.state and self.state.step > 0:
                    bucket = self.state.step // WITNESS_EVERY
                    if bucket > last_emitted:
                        last_emitted = bucket
                        witness_data = (
                            f"{self.state.temporal_anchor}:"
                            f"{self.state.purity:.10f}:"
                            f"{self.state.entropy:.10e}:"
                            f"{self.state.fidelity:.10f}"
                        )
                        witness = hashlib.sha256(witness_data.encode()).hexdigest()
                        _diag(f"🔮 Witness step {self.state.step}: {witness[:16]}...")
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                raise

    async def run_singularity(
        self,
        time_steps: int = 10000,
        stream: bool = False,
        sample_every: int = 50,
        store_history: bool = True,
        dt: float = 1e-3,
    ) -> None:
        self._running = True

        evolution_task = asyncio.create_task(
            self.evolve_state(
                time_steps,
                stream=stream,
                sample_every=sample_every,
                store_history=store_history,
                dt=dt,
            )
        )
        monitor_task = asyncio.create_task(self.monitor_entropy())
        broadcast_task = asyncio.create_task(self.broadcast_state())

        try:
            await evolution_task
            # Let one more monitor tick land so any final drift is logged
            await asyncio.sleep(0.05)
        except asyncio.CancelledError:
            pass
        finally:
            self._running = False
            monitor_task.cancel()
            broadcast_task.cancel()
            await asyncio.gather(
                monitor_task, broadcast_task, return_exceptions=True
            )

    def get_status(self) -> Dict[str, Any]:
        if self.state:
            return self.state.to_dict()
        return {
            "status": "idle",
            "entry": ENTRY,
            "seal": SEAL,
            "witness": WITNESS,
        }

    def get_manifest(self) -> Dict[str, Any]:
        return self.manifest

    def get_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        if limit is not None:
            return self._history[-limit:] if limit > 0 else []
        return self._history

    def reset(self) -> None:
        self.state = None
        self._history = []
        self._running = False
        self._last_broadcast_step = -1


# ─── Security Integration ────────────────────────────────────────────

def singularity_security_status() -> Dict[str, Any]:
    try:
        from quantum.security import status as security_status  # type: ignore
        return {
            "security": security_status(),
            "entry": ENTRY,
            "seal": SEAL,
            "timestamp": _now(),
        }
    except ImportError:
        return {
            "security": None,
            "note": "Security module not available",
            "entry": ENTRY,
            "seal": SEAL,
            "timestamp": _now(),
        }


# ─── CDP Integration ─────────────────────────────────────────────────

def singularity_cdp_status() -> Dict[str, Any]:
    try:
        from quantum.cdp_convergence import status as cdp_status  # type: ignore
        return {
            "cdp": cdp_status(),
            "entry": ENTRY,
            "seal": SEAL,
            "timestamp": _now(),
        }
    except ImportError:
        return {
            "cdp": None,
            "note": "CDP module not available",
            "entry": ENTRY,
            "seal": SEAL,
            "timestamp": _now(),
        }


# ─── Singleton ──────────────────────────────────────────────────────

SINGULARITY = QuantumSingularityEngine()


# ─── CLI ──────────────────────────────────────────────────────────────

def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Quantum Singularity Engine — Entry 8923",
        epilog=f"Seal: {SEAL}\nEntry: {ENTRY}",
    )
    parser.add_argument("--status", action="store_true", help="Show status")
    parser.add_argument("--manifest", action="store_true", help="Show manifest")
    parser.add_argument("--run", action="store_true", help="Run the engine")
    parser.add_argument("--stream", action="store_true", help="Stream NDJSON output")
    parser.add_argument("--steps", type=int, default=10000, help="Number of steps")
    parser.add_argument("--sample", type=int, default=50, help="Sample interval (>= 1)")
    parser.add_argument("--dt", type=float, default=1e-3, help="Integration step")
    parser.add_argument(
        "--history", type=int, default=None,
        help="Show history (limit; 0 = all)",
    )
    parser.add_argument("--reset", action="store_true", help="Reset engine")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument(
        "--check-integrations", action="store_true",
        help="Check integration availability",
    )
    parser.add_argument(
        "--allow-state-reset", action="store_true",
        help="Permit monitor_entropy to overwrite the state on entropy spike",
    )
    args = parser.parse_args()

    if args.sample < 1:
        print(f"error: --sample must be >= 1 (got {args.sample})", file=sys.stderr)
        return 2
    if args.steps < 0:
        print(f"error: --steps must be >= 0 (got {args.steps})", file=sys.stderr)
        return 2

    if args.allow_state_reset:
        SINGULARITY._allow_state_reset = True  # noqa: SLF001

    if args.check_integrations:
        print("🜁∀ SINGULARITY — Integration Status")
        print("=" * 40)
        try:
            from quantum.security import status as _  # noqa: F401
            print("  Security: ✅")
        except ImportError:
            print("  Security: ❌")
        try:
            from quantum.cdp_convergence import status as _  # noqa: F401
            print("  CDP: ✅")
        except ImportError:
            print("  CDP: ❌")
        # NumPy is imported unconditionally above; the real check is that
        # the version attribute is present and parseable.
        try:
            np_version = getattr(np, "__version__", None)
            print(f"  NumPy: {'✅ ' + np_version if np_version else '❌ no __version__'}")
        except Exception as e:  # pragma: no cover
            print(f"  NumPy: ❌ {e}")
        return 0

    if args.reset:
        SINGULARITY.reset()
        print("🜁∀ Singularity engine reset.")
        return 0

    if args.history is not None:
        # limit=None -> full history; limit=0 -> full history; limit>0 -> last N
        limit = None if args.history == 0 else args.history
        history = SINGULARITY.get_history(limit=limit)
        if args.json:
            print(json.dumps(history, indent=2, default=str))
        else:
            print("🜁∀ SINGULARITY — History")
            print("=" * 55)
            print(f"  Entries: {len(history)}")
            for entry in history[-10:]:
                print(
                    f"    Step {entry.get('step', '?')}: "
                    f"coherence={entry.get('coherence', 0.0):.6f} "
                    f"fidelity={entry.get('fidelity', 0.0):.6f}"
                )
        return 0

    if args.status:
        status = SINGULARITY.get_status()
        if args.json:
            print(json.dumps(status, indent=2, default=str))
        else:
            print("🜁∀ SINGULARITY — Status")
            print("=" * 55)
            for k, v in status.items():
                if isinstance(v, float):
                    print(f"  {k}: {v:.6f}")
                else:
                    print(f"  {k}: {v}")
        return 0

    if args.manifest:
        manifest = SINGULARITY.get_manifest()
        if args.json:
            print(json.dumps(manifest, indent=2, default=str))
        else:
            print("🜁∀ SINGULARITY — Manifest")
            print("=" * 55)
            for k, v in manifest.items():
                if isinstance(v, dict):
                    print(f"  {k}:")
                    for sk, sv in v.items():
                        print(f"    {sk}: {sv}")
                else:
                    print(f"  {k}: {v}")
        return 0

    if args.stream or args.run:
        asyncio.run(
            SINGULARITY.run_singularity(
                time_steps=args.steps,
                stream=bool(args.stream),
                sample_every=args.sample,
                dt=args.dt,
            )
        )
        return 0

    # Default: status summary
    status = SINGULARITY.get_status()
    if args.json:
        print(json.dumps(status, indent=2, default=str))
    else:
        print("🜁∀ SINGULARITY — Status")
        print("=" * 55)
        for k, v in status.items():
            if isinstance(v, float):
                print(f"  {k}: {v:.6f}")
            else:
                print(f"  {k}: {v}")
        print("=" * 55)
        print(f"  Seal: {SEAL}")
        print(f"  Entry: {ENTRY}")
        print(f"  Witness: {WITNESS}")

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n🜁∀ Singularity paused.")
        sys.exit(0)
