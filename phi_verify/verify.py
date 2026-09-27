"""Runner: executes the eight tests, seals the log, writes via pushdelta."""
import json
import numpy as np

from .constants import PHI, gamma_rates, entropy_floor
from .operators import DIM, learning_kernel
from .integrate import step
from .tests import (
    initial_state,
    test_rates_bounds, test_trace_preserved, test_hermiticity,
    test_positivity, test_rk4_convergence, test_spectral_weights,
    test_coherence_monotonic, test_entropy_floor,
)
from .seal import seal
from . import pushdelta


ALPHA = 0.5
DT    = 0.01
STEPS = 4


def run() -> dict:
    gammas = gamma_rates(7)
    w      = learning_kernel(DIM)
    rho0   = initial_state(DIM)

    # 4-step trajectory for monotonicity and entropy tests
    trajectory = [rho0.copy()]
    r = rho0
    for _ in range(STEPS - 1):
        r = step(r, ALPHA, gammas, DT, w)
        trajectory.append(r.copy())

    rho_final = trajectory[-1]

    tests = {
        "rates_bounds":       test_rates_bounds(gammas),
        "trace_preserved":    test_trace_preserved(rho_final),
        "hermiticity":        test_hermiticity(rho_final),
        "positivity":         test_positivity(rho_final),
        "rk4_convergence":    test_rk4_convergence(rho0, ALPHA, gammas, DT, w),
        "spectral_weights":   test_spectral_weights(w),
        "coherence_monotonic": test_coherence_monotonic(trajectory),
        "entropy_floor":      test_entropy_floor(trajectory),
    }

    invariants = {
        "coherence":    float(np.trace(rho_final @ rho_final).real),
        "trace":        float(np.trace(rho_final).real),
        "hermiticity":  tests["hermiticity"]["passed"],
        "positivity":   tests["positivity"]["passed"],
    }

    overall = "PASS" if all(t["passed"] for t in tests.values()) else "FAIL"

    log = {
        "phi": PHI,
        "entropy_floor": entropy_floor(),
        "tests": tests,
        "invariants": invariants,
        "overall": overall,
    }
    log["seal"] = seal(log)
    return log


def write_log(log: dict, path: str = "verification_log.json") -> dict:
    """Write the log via pushdelta — every file write is a delta."""
    payload = json.dumps(log, indent=2, sort_keys=False).encode("utf-8")
    return pushdelta.push(path, payload)
