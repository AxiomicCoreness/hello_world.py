"""
Dexterity Index with Heal Resilience Factor

The dexterity index measures the system's ability to self-correct and adapt.
It now includes a heal-resilience factor based on the octonion heal loop performance.
"""

from datetime import datetime, timezone
import math

PHI = (1 + math.sqrt(5)) / 2


def compute_heal_resilience(healer):
    """
    Compute the heal resilience factor for the dexterity index.
    
    Args:
        healer: OctonionSelfHealer instance
        
    Returns:
        float: Heal resilience factor (0-1)
    """
    # Base: success_rate, adjusted by heal_count / age
    age_hours = (datetime.now(timezone.utc) - healer.start_time).total_seconds() / 3600
    return healer.success_rate * math.exp(-0.01 * age_hours)


def compute_dexterity_index(healer, coherence=1.0, entropy=0.0, phase_lock=0.0):
    """
    Compute the overall dexterity index.
    
    Args:
        healer: OctonionSelfHealer instance
        coherence: System coherence value (0-1)
        entropy: System entropy value
        phase_lock: Phase lock angle in degrees
        
    Returns:
        float: Dexterity index
    """
    # Heal resilience factor
    heal_resilience = compute_heal_resilience(healer)
    
    # φ-harmonic invariants
    # Coherence 1.0, Entropy φ⁻¹⁴¹⁸, Phase Lock 202.6°
    target_entropy = PHI ** (-1418)
    target_phase_lock = 202.6
    
    # Normalize entropy and phase lock
    entropy_score = 1.0 - abs(entropy - target_entropy) / (target_entropy + 1e-10)
    phase_score = 1.0 - abs(phase_lock - target_phase_lock) / 360.0
    
    # Weighted combination
    dexterity = (
        0.3 * coherence +
        0.2 * entropy_score +
        0.2 * phase_score +
        0.3 * heal_resilience
    )
    
    return dexterity


class DexterityMonitor:
    """Monitor and track dexterity index over time."""
    
    def __init__(self, healer):
        self.healer = healer
        self.history = []
        self.max_history = 100
    
    def update(self, coherence=1.0, entropy=0.0, phase_lock=0.0):
        """Update dexterity index with current values."""
        dexterity = compute_dexterity_index(
            self.healer, 
            coherence=coherence, 
            entropy=entropy, 
            phase_lock=phase_lock
        )
        timestamp = datetime.now(timezone.utc).isoformat()
        self.history.append({
            'timestamp': timestamp,
            'dexterity': dexterity,
            'coherence': coherence,
            'entropy': entropy,
            'phase_lock': phase_lock,
            'heal_resilience': compute_heal_resilience(self.healer)
        })
        
        if len(self.history) > self.max_history:
            self.history.pop(0)
        
        return dexterity
    
    def get_history(self):
        """Get dexterity history."""
        return self.history
    
    def get_current(self):
        """Get current dexterity index."""
        if self.history:
            return self.history[-1]['dexterity']
        return 0.0