"""
Reward Protocol for Sovereign Swarm
Entry 8339 - Approved by Commander Clarke Yoursa Tee
Witness Chain: 8339 -> 8340 -- UNBROKEN
Seal: ∀∞φ² · REWARD_PROTOCOL · SEALED

SPU (Sovereign Power Unit) Definition:
- Normalized scalar reward in [0, 1]
- Aggregated from n sub-metrics m = (m₁, ..., mₙ)
- Weights w ∈ Δⁿ⁻¹ (non-negative, sum to 1)

Three aggregation modes:
- Linear:     SPU_lin = w · m
- Geometric:  SPU_geo = Πᵢ mᵢ^{wᵢ}  (punishes any zero)
- Harmonic:   SPU_har = (Σᵢ wᵢ / mᵢ)⁻¹  (requires mᵢ > 0)

φ-harmonic variant:
- wᵢ ∝ φ^(−i), normalized
- τ_hi = φ⁻¹ ≈ 0.618
- τ_lo = φ⁻² ≈ 0.382
- φ = (1+√5)/2
"""

from dataclasses import dataclass
from typing import Sequence, Optional, Literal
import math

# Golden ratio
PHI = (1 + math.sqrt(5)) / 2
PHI_INV = 1 / PHI  # ≈ 0.618
PHI_INV_2 = 1 / (PHI ** 2)  # ≈ 0.382


@dataclass(frozen=True)
class Gate:
    """Pass/Fail gate with hysteresis"""
    tau_hi: float = PHI_INV      # Upper threshold
    tau_lo: float = PHI_INV_2    # Lower threshold
    eps: float = 0.05            # Drift tolerance


@dataclass(frozen=True)
class SPUConfig:
    """SPU configuration"""
    mode: Literal["linear", "geometric", "harmonic"] = "linear"
    weights: Optional[Sequence[float]] = None
    phi_harmonic: bool = False


def normalize_weights(weights: Sequence[float]) -> Sequence[float]:
    """Normalize weights to sum to 1"""
    total = sum(weights)
    if total <= 0:
        raise ValueError("Weights must sum to positive value")
    return [w / total for w in weights]


def phi_harmonic_weights(n: int) -> Sequence[float]:
    """Generate φ-harmonic weights: wᵢ ∝ φ^(−i)"""
    weights = [PHI ** (-i) for i in range(1, n + 1)]
    return normalize_weights(weights)


def spu(m: Sequence[float], w: Sequence[float], mode: str = "linear") -> float:
    """
    Compute SPU (Sovereign Power Unit) from metrics and weights.
    
    Args:
        m: Sequence of metrics, each in [0, 1]
        w: Sequence of weights, non-negative, sum to 1
        mode: Aggregation mode - "linear", "geometric", or "harmonic"
    
    Returns:
        SPU value in [0, 1]
    """
    # Validate inputs
    if len(m) != len(w):
        raise ValueError(f"Length mismatch: m has {len(m)} elements, w has {len(w)}")
    if abs(sum(w) - 1.0) > 1e-9:
        raise ValueError("Weights must sum to 1")
    if any(x < 0 or x > 1 for x in m):
        raise ValueError("All metrics must be in [0, 1]")
    if any(x < 0 for x in w):
        raise ValueError("All weights must be non-negative")
    
    if mode == "linear":
        return sum(wi * mi for wi, mi in zip(w, m))
    
    elif mode == "geometric":
        # Geometric mean: Πᵢ mᵢ^{wᵢ}
        # Punishes any zero metric
        product = 1.0
        for wi, mi in zip(w, m):
            if mi == 0:
                return 0.0  # Any zero makes geometric SPU zero
            product *= mi ** wi
        return product
    
    elif mode == "harmonic":
        # Harmonic mean: (Σᵢ wᵢ / mᵢ)⁻¹
        # Requires all mᵢ > 0
        if any(mi == 0 for mi in m):
            raise ValueError("Harmonic mode requires all metrics > 0")
        return 1.0 / sum(wi / mi for wi, mi in zip(w, m))
    
    else:
        raise ValueError(f"Unknown mode: {mode}")


def bounded_reward(spu_val: float, budget: float) -> float:
    """
    Compute bounded reward R = B · SPU
    
    Args:
        spu_val: SPU value in [0, 1]
        budget: Budget B per episode
    
    Returns:
        Reward R in [0, B]
    """
    return budget * spu_val


def pass_fail_gate(spu_val: float, gate: Gate) -> Literal["PASS", "FAIL", "HOLD"]:
    """
    Pass/fail gate with hysteresis to prevent flapping.
    
    Args:
        spu_val: SPU value
        gate: Gate configuration with tau_hi, tau_lo, eps
    
    Returns:
        "PASS" if SPU ≥ τ_hi
        "FAIL" if SPU ≤ τ_lo
        "HOLD" otherwise
    """
    if spu_val >= gate.tau_hi:
        return "PASS"
    elif spu_val <= gate.tau_lo:
        return "FAIL"
    else:
        return "HOLD"


def drift_check(spu_on: float, spu_off: float, gate: Gate) -> tuple[bool, float]:
    """
    Check for drift between online and offline SPU.
    
    Args:
        spu_on: SPU from live telemetry
        spu_off: SPU from replay/simulation
        gate: Gate configuration with eps
    
    Returns:
        Tuple of (is_drift, delta) where delta = |SPU_on - SPU_off|
    """
    delta = abs(spu_on - spu_off)
    is_drift = delta > gate.eps
    return is_drift, delta


def verdict(spu_on: float, spu_off: float, gate: Gate) -> Literal["PASS", "FAIL", "HOLD", "DRIFT", "VETO"]:
    """
    Compute sidecar verdict based on SPU values.
    
    Args:
        spu_on: SPU from live telemetry
        spu_off: SPU from replay/simulation
        gate: Gate configuration
    
    Returns:
        Verdict: PASS, FAIL, HOLD, DRIFT, or VETO
    
    Rules:
    1. Sidecar can only downgrade (turn PASS into HOLD or DRIFT, never upgrade FAIL)
    2. Timeout = HOLD (fail-safe, not fail-open)
    3. Independent code path from main loop
    """
    # First check for drift
    is_drift, delta = drift_check(spu_on, spu_off, gate)
    if is_drift:
        return "DRIFT"
    
    # Then check pass/fail
    if spu_on >= gate.tau_hi:
        return "PASS"
    elif spu_on <= gate.tau_lo:
        return "FAIL"
    else:
        return "HOLD"


class RewardProtocol:
    """
    Main reward protocol class implementing the three-loop system.
    
    Loop 1 (Inner): Per-step, milliseconds - Observe and compute metrics
    Loop 2 (Middle): Per-episode, seconds - Aggregate and compute SPU
    Loop 3 (Outer): Per-N episodes, hours - Update weights and thresholds
    Sidecar: Independent process - Veto capability
    """
    
    def __init__(self, config: SPUConfig, gate: Optional[Gate] = None):
        self.config = config
        self.gate = gate or Gate()
        self.ring_buffer: list[Sequence[float]] = []
        self.episode_counter = 0
        self.verdicts: list[Literal["PASS", "FAIL", "HOLD", "DRIFT", "VETO"]] = []
    
    def observe_step(self, metrics: Sequence[float]) -> None:
        """
        Loop 1: Observe step and store metrics in ring buffer.
        
        Args:
            metrics: Sequence of metric values for this step
        """
        self.ring_buffer.append(metrics)
    
    def compute_spu(self) -> float:
        """
        Loop 2: Aggregate metrics from ring buffer and compute SPU.
        
        Returns:
            SPU value
        """
        if not self.ring_buffer:
            return 0.0
        
        # Average metrics across all steps in buffer
        n_metrics = len(self.ring_buffer[0])
        n_steps = len(self.ring_buffer)
        
        avg_metrics = [0.0] * n_metrics
        for step_metrics in self.ring_buffer:
            for i, val in enumerate(step_metrics):
                avg_metrics[i] += val
        
        avg_metrics = [m / n_steps for m in avg_metrics]
        
        # Use configured weights or generate φ-harmonic weights
        weights = self.config.weights
        if weights is None:
            weights = phi_harmonic_weights(n_metrics)
        
        return spu(avg_metrics, weights, self.config.mode)
    
    def process_episode(self, budget: float) -> tuple[float, Literal["PASS", "FAIL", "HOLD"]]:
        """
        Process an episode: compute SPU, determine verdict, compute reward.
        
        Args:
            budget: Budget B for this episode
        
        Returns:
            Tuple of (reward, verdict)
        """
        spu_val = self.compute_spu()
        verdict_val = pass_fail_gate(spu_val, self.gate)
        reward = bounded_reward(spu_val, budget)
        
        self.verdicts.append(verdict_val)
        self.episode_counter += 1
        self.ring_buffer.clear()
        
        return reward, verdict_val
    
    def sidecar_verdict(self, spu_on: float, spu_off: float) -> Literal["PASS", "FAIL", "HOLD", "DRIFT", "VETO"]:
        """
        Sidecar independent verification.
        
        Args:
            spu_on: SPU from main loop (live telemetry)
            spu_off: SPU from sidecar (replay/simulation)
        
        Returns:
            Sidecar verdict
        """
        return verdict(spu_on, spu_off, self.gate)
    
    def update_outer_loop(self, n_episodes: int = 100) -> None:
        """
        Loop 3: Update weights and thresholds based on collected verdicts.
        
        Args:
            n_episodes: Number of episodes to analyze
        """
        if len(self.verdicts) < n_episodes:
            return
        
        # Analyze recent verdicts
        recent_verdicts = self.verdicts[-n_episodes:]
        pass_rate = recent_verdicts.count("PASS") / n_episodes
        fail_rate = recent_verdicts.count("FAIL") / n_episodes
        
        # Adjust thresholds based on performance
        # This is a simple example - actual implementation would be more sophisticated
        if pass_rate > 0.8:
            # Too many passes, increase thresholds
            self.gate = Gate(
                tau_hi=min(self.gate.tau_hi * 1.05, 0.95),
                tau_lo=min(self.gate.tau_lo * 1.05, self.gate.tau_hi - 0.05),
                eps=self.gate.eps
            )
        elif fail_rate > 0.3:
            # Too many fails, decrease thresholds
            self.gate = Gate(
                tau_hi=max(self.gate.tau_hi * 0.95, 0.1),
                tau_lo=max(self.gate.tau_lo * 0.95, 0.05),
                eps=self.gate.eps
            )
    
    def timescale_stability_check(self, rates: dict[str, float]) -> bool:
        """
        Verify loop stability condition: rate(L3) ≤ 0.1 · rate(L2) ≤ 0.01 · rate(L1)
        
        Args:
            rates: Dictionary with keys "L1", "L2", "L3" and values in Hz
        
        Returns:
            True if timescales are properly separated, False otherwise
        """
        if "L1" not in rates or "L2" not in rates or "L3" not in rates:
            return False
        
        l1_rate = rates["L1"]
        l2_rate = rates["L2"]
        l3_rate = rates["L3"]
        
        # Check L2 ≤ 0.01 * L1
        if l2_rate > 0.01 * l1_rate:
            return False
        
        # Check L3 ≤ 0.1 * L2
        if l3_rate > 0.1 * l2_rate:
            return False
        
        return True


if __name__ == "__main__":
    # Example usage
    print("Reward Protocol - Example Usage")
    print("=" * 50)
    
    # Create protocol with φ-harmonic configuration
    config = SPUConfig(mode="linear", phi_harmonic=True)
    protocol = RewardProtocol(config)
    
    # Simulate some metrics
    metrics = [
        [0.8, 0.7, 0.9],
        [0.85, 0.75, 0.95],
        [0.78, 0.72, 0.88]
    ]
    
    for m in metrics:
        protocol.observe_step(m)
    
    # Process episode
    reward, verdict = protocol.process_episode(budget=100.0)
    print(f"SPU: {protocol.compute_spu():.4f}")
    print(f"Verdict: {verdict}")
    print(f"Reward: {reward:.2f}")
    
    # Test sidecar
    spu_on = protocol.compute_spu()
    spu_off = spu_on * 0.98  # Slight drift
    sidecar_verdict = protocol.sidecar_verdict(spu_on, spu_off)
    print(f"Sidecar Verdict: {sidecar_verdict}")
    
    # Test timescale stability
    rates = {"L1": 1000.0, "L2": 10.0, "L3": 0.1}
    stable = protocol.timescale_stability_check(rates)
    print(f"Timescale Stability: {stable}")
