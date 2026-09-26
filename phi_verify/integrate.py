"""One-shot and RK4 integration of the concatenation update."""
import numpy as np

from .operators import attenuation, learning_kernel


def step(rho, alpha, gammas, dt, w):
    """
    ρ_{t+1} = (1-α)·D(ρ_t) + α·(ρ_t ⊙ w)

    The Hadamard product ⊙ is applied elementwise; w is broadcast as
    a matrix of the same shape as ρ.
    """
    return (1.0 - alpha) * attenuation(rho, gammas, dt) + alpha * (rho * w)


def rk4_step(rho, alpha, gammas, dt, w):
    """One RK4 step of dρ/dt = f(ρ), where f is step() minus identity, scaled by 1/dt."""
    def f(r):
        return (step(r, alpha, gammas, dt, w) - r) / dt

    k1 = f(rho)
    k2 = f(rho + (dt / 2.0) * k1)
    k3 = f(rho + (dt / 2.0) * k2)
    k4 = f(rho +  dt        * k3)
    return rho + (dt / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)
