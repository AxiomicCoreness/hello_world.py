"""
Verifier Worker with Octonion Heal Loop Integration

This module provides the verifier worker that checks system integrity
and integrates with the self-improving octonion heal loop.
"""

from octonion_self_healer import OctonionSelfHealer
import time
import threading

# Global self-healer instance
self_healer = OctonionSelfHealer()

# Heal loop status gauge for Prometheus
_octonion_heal_loop_status = 1  # 1 = healthy, 0 = healing


def octonion_heal_loop(engine):
    """
    Run the octonion heal loop check.
    
    Args:
        engine: The Sovereign Engine instance
        
    Returns:
        True if stable, False if healing was performed
    """
    global _octonion_heal_loop_status
    
    try:
        result = self_healer.check_and_heal(engine)
        _octonion_heal_loop_status = 1 if result else 0
        return result
    except Exception as e:
        # Log error and mark as unhealthy
        _octonion_heal_loop_status = 0
        if hasattr(engine, 'logger'):
            engine.logger.error(f"Octonion heal loop error: {e}")
        return False


def get_octonion_heal_loop_status():
    """Get current heal loop status (1 = healthy, 0 = healing)."""
    return _octonion_heal_loop_status


def get_self_healer():
    """Get the global self-healer instance."""
    return self_healer


class HealLoopMonitor(threading.Thread):
    """
    Background thread to monitor and run the heal loop periodically.
    Breathes at NORTH_STAR_FREQ (71.975 Hz).
    """
    
    NORTH_STAR_FREQ = 71.975  # Hz
    
    def __init__(self, engine, interval=1.0/NORTH_STAR_FREQ):
        super().__init__()
        self.engine = engine
        self.interval = interval
        self.running = False
        
    def run(self):
        """Run the heal loop monitor."""
        self.running = True
        while self.running:
            octonion_heal_loop(self.engine)
            time.sleep(self.interval)
    
    def stop(self):
        """Stop the monitor."""
        self.running = False