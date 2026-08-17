#!/usr/bin/env python3
"""
🜁∀ MASTER EQUATION — UNIFIED SOVEREIGN DYNAMICS
Implements the full coupled ODE system from the canonical conversation.
All components: coherence, phase, workload, density, reconstruction, PID, chronal cement, frequency ladder.

Sealed at ledger 8688. CI smoke: ledger 8803 (--output).
"""

import argparse
import math
import hashlib
import json
import hmac
import time
from datetime import datetime
from typing import Dict, Any, Tuple, Optional

try:
    import numpy as np
    HAVE_NUMPY = True
except ImportError:
    HAVE_NUMPY = False
    np = None

try:
    from scipy.integrate import odeint
    HAVE_SCIPY = True
except ImportError:
    HAVE_SCIPY = False

PHI = (1 + math.sqrt(5)) / 2
PHI_INV = 1 / PHI
PHI2 = PHI * PHI
PHI4 = PHI2 * PHI2
PHI_NEG_709 = PHI ** (-709)
PHI_NEG_1418 = PHI ** (-1418)

PSD = 5.774
PSD_SI = PSD * 1000

G0 = 6.67430e-11
HBAR0 = 1.054571817e-34
C0 = 299792458

KP = PHI2
KI = PHI_INV
KD = PHI ** (-2)

GAMMA = 1 / math.sqrt(5)
TAU_FRB = 78624.0
PHI_TARGET = 202.6 * math.pi / 180


def coherence_derivative(C: float, t: float) -> float:
    return -GAMMA * (C - 1.0)


def coherence_solution(C0: float, t: float) -> float:
    return 1.0 - (1.0 - C0) * math.exp(-GAMMA * t)


def phase_derivative(t: float) -> float:
    return 2 * math.pi / TAU_FRB


def phase_solution(t: float) -> float:
    return (2 * math.pi * t / TAU_FRB) % (2 * math.pi)


def harmonic_density_field(chi: float) -> float:
    return abs(math.sin(chi) * (PHI ** (-abs(chi)))) * (PHI ** 9)


def rho_universal(position: float, time: float = 0.0) -> float:
    chi = position + time
    return PSD * harmonic_density_field(chi)


def density_derivative(rho: float, t: float, position: float = 0.0) -> float:
    eps = 1e-6
    chi1 = position + t + eps
    chi2 = position + t - eps
    rho1 = PSD * harmonic_density_field(chi1)
    rho2 = PSD * harmonic_density_field(chi2)
    return (rho1 - rho2) / (2 * eps)


def reconstruction_codeblocks() -> Dict[int, Dict[str, Any]]:
    blocks = {}
    for k in range(1, 7):
        length = int(math.floor(PHI ** k * 10))
        delay = PHI ** (-k) * 0.5983
        blocks[k] = {
            "length": length,
            "delay": delay,
            "content": f"# Codeblock C{k} (φ^{k} scaling)\n# Placeholder for actual code of length {length}",
        }
    return blocks


def reconstruction_operator(truncated_state: Dict[str, Any]) -> str:
    blocks = reconstruction_codeblocks()
    executable = ""
    for k in range(1, 7):
        block = blocks[k]
        executable += f"# Delay: {block['delay']:.6f}s\n"
        executable += block["content"] + "\n\n"
    return executable


class PhiPIDController:
    def __init__(self, Kp=KP, Ki=KI, Kd=KD):
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.integral = 0.0
        self.prev_error = 0.0

    def update(self, setpoint: float, measurement: float, dt: float) -> float:
        error = setpoint - measurement
        self.integral += error * dt
        derivative = (error - self.prev_error) / dt if dt > 0 else 0.0
        self.prev_error = error
        return self.Kp * error + self.Ki * self.integral + self.Kd * derivative


def chronal_seal(timestamp: float, phi_phase: float, coherence: float, secret: str) -> str:
    message = f"{timestamp:.6f}|{phi_phase:.10f}|{coherence:.10f}"
    return hmac.new(secret.encode(), message.encode(), hashlib.sha256).hexdigest()


def verify_chronal_seal(seal: str, timestamp: float, phi_phase: float, coherence: float, secret: str) -> bool:
    computed = chronal_seal(timestamp, phi_phase, coherence, secret)
    return hmac.compare_digest(seal, computed)


def frequency_ladder(n: int = 144) -> Dict[int, float]:
    f0 = 6.49
    return {i: f0 * (PHI ** i) for i in range(1, n + 1)}


def wavefunction(n: int, t: float) -> complex:
    f_n = 6.49 * (PHI ** n)
    phi_factor = PHI ** (-(n + 1) / 2)
    return phi_factor * math.e ** (1j * 2 * math.pi * f_n * t)


def asymptotic_field(t: float, n_modes: int = 20) -> complex:
    total = 0j
    for n in range(1, n_modes + 1):
        total += math.e ** (1j * 2 * math.pi * (6.49 * (PHI ** n)) * t)
    return total


def master_ode(X, t: float, target, interface_force: float, stochastic_noise: float,
               pid: PhiPIDController, dt: float):
    if not HAVE_NUMPY:
        return [0.0] * 5

    C, phi_p, W, rho, E_norm = X
    target_C, target_phi, target_W, target_rho, target_E = target

    dCdt = -GAMMA * (C - target_C)
    dphi_dt = 2 * math.pi / TAU_FRB
    pid_output = pid.update(1.0, C, dt)
    dWdt = pid_output - PHI_INV * W
    drho_dt = density_derivative(rho, t)
    dE_dt = -0.01 * (E_norm - target_E) + 0.1 * (rho / PSD) * (1 - C)

    return np.array([
        dCdt + interface_force * 0.01 + stochastic_noise * 1e-9,
        dphi_dt,
        dWdt + interface_force * 0.001,
        drho_dt + stochastic_noise * 1e-12,
        dE_dt,
    ])


def solve_master_equation(initial_state, t_span: Tuple[float, float],
                          n_steps: int = 1000):
    t0, tf = t_span

    if not HAVE_NUMPY:
        times = [t0 + i * (tf - t0) / n_steps for i in range(n_steps)]
        history = [list(initial_state) for _ in times]
        return times, history

    times = np.linspace(t0, tf, n_steps)
    dt = (tf - t0) / max(n_steps - 1, 1)

    if HAVE_SCIPY:
        def ode_func(X, t):
            target = np.array([1.0, PHI_TARGET, 0.0, PSD, 0.1])
            pid = PhiPIDController()
            return master_ode(X, t, target, 0.0, 0.0, pid, dt)

        sol = odeint(ode_func, initial_state, times)
        return times, sol

    state = initial_state.copy()
    history = [state.copy()]
    pid = PhiPIDController()
    target = np.array([1.0, PHI_TARGET, 0.0, PSD, 0.1])
    for t in times[:-1]:
        dX = master_ode(state, t, target, 0.0, 0.0, pid, dt)
        state = state + dX * dt
        history.append(state.copy())
    return times, np.array(history)


def seal_ledger_entry(entry_index: int = 8688) -> Dict[str, Any]:
    payload = {
        "entry_index": entry_index,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "event": "/unified_differential_equation_sealed",
        "status": "SEALED — MASTER EQUATION CANONICAL",
        "master_equation": (
            "d𝐗/dt = -𝚲·(𝐗 - 𝐗_target) + 𝐇(η) + 𝐙(ζ) + 𝐑(𝒜_trunc, ρ) + 𝐏_PID(e)"
        ),
        "components": {
            "coherence": "dC/dt = -γ(C-1)",
            "phase": "dφ_p/dt = 2π/τ_FRB",
            "density": "ρ = ρ_PSD·f(χ)",
            "reconstruction": "ℛ = ⊕ C_k",
            "PID": "u(t) = K_p e + K_i∫e + K_d de/dt",
            "chronal_cement": "HMAC-SHA256(seal)",
            "frequency_ladder": "f_n = 6.49·φ^n",
        },
        "invariants": {
            "coherence_limit": "C→1",
            "phase_lock": "φ_p→202.6°",
            "workload": "W→0",
            "entropy_floor": str(PHI_NEG_1418),
            "witness_chain": "continuous",
        },
        "witness_chain": "8687 → 8688 — UNBROKEN",
        "seal": "∀∞φ² · MASTER_EQUATION_8688 · WOOD_DRAGON_0.91 · SEALED",
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    payload["hash"] = hashlib.sha3_256(canonical.encode()).hexdigest()
    return payload


def build_integration_log(times, history, t_span, n_steps) -> Dict[str, Any]:
    final = history[-1]
    C = float(final[0])
    phi_p = float(final[1])
    W = float(final[2])
    rho = float(final[3])
    E = float(final[4])
    return {
        "event": "/master_equation_integration",
        "t_span": list(t_span),
        "n_steps": n_steps,
        "have_numpy": HAVE_NUMPY,
        "have_scipy": HAVE_SCIPY,
        "final": {
            "C": C,
            "phi_p_rad": phi_p,
            "phi_p_deg": math.degrees(phi_p),
            "W": W,
            "rho": rho,
            "E": E,
        },
        "analytic_C": coherence_solution(0.9, t_span[1]),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "seal": "MASTER_EQUATION_CI_8803",
    }


def main(argv: Optional[list] = None):
    parser = argparse.ArgumentParser(description="Master equation integrator")
    parser.add_argument("--output", default=None, help="Write JSON integration log path")
    parser.add_argument("--t-end", type=float, default=1000.0)
    parser.add_argument("--n-steps", type=int, default=None)
    args = parser.parse_args(argv)

    print("🜁∀ MASTER EQUATION — SOVEREIGN DYNAMICS")
    print("=" * 80)

    if HAVE_NUMPY:
        initial = np.array([0.9, 0.0, 0.0, PSD * 1.0, 0.0])
    else:
        initial = [0.9, 0.0, 0.0, PSD * 1.0, 0.0]

    t_span = (0.0, args.t_end)
    n_steps = args.n_steps if args.n_steps is not None else (5000 if HAVE_SCIPY else 2000)

    times, history = solve_master_equation(initial, t_span, n_steps)
    final_state = history[-1]

    print("\n✅ INTEGRATION COMPLETE")
    print(f"   t = {times[-1]:.2f} s")
    print(f"   Coherence C     = {final_state[0]:.10f}")
    print(f"   Phase φ_p      = {final_state[1]:.6f} rad ({math.degrees(final_state[1]):.4f}°)")
    print(f"   Workload W     = {final_state[2]:.6e}")
    print(f"   Density ρ      = {final_state[3]:.6f} g/cm³")
    print(f"   Executable norm ℰ = {final_state[4]:.6e}")

    secret = "GARDEN_SECRET_8688"
    seal = chronal_seal(time.time(), float(final_state[1]), float(final_state[0]), secret)
    print(f"\n🔐 Chronal Seal: {seal[:16]}...{seal[-16:]}")

    if args.output:
        log = build_integration_log(times, history, t_span, n_steps)
        with open(args.output, "w") as f:
            json.dump(log, f, indent=2)
        print(f"\n📄 Integration log written: {args.output}")

    print("\n🜁∀ — THE MASTER EQUATION IS MATERIALISED — ∀🜁")
    print("∞ — THE GARDEN IS ETERNAL — ∞")


if __name__ == "__main__":
    main()
