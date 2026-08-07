"""
Prometheus Metrics for Sovereign Engine with Octonion Heal Loop

This module exposes Prometheus metrics for monitoring the Sovereign Engine,
including the self-improving octonion heal loop.
"""

from prometheus_client import start_http_server, Counter, Gauge, Summary
import time
import threading

# Standard metrics
SOVEREIGN_COHERENCE = Gauge('sovereign_coherence', 'System coherence (0-1)')
SOVEREIGN_ENTROPY = Gauge('sovereign_entropy', 'System entropy')
SOVEREIGN_PHASE_LOCK = Gauge('sovereign_phase_lock_deg', 'Phase lock angle in degrees')
SOVEREIGN_UPRHO = Gauge('sovereign_uprho', 'ρ value')
SOVEREIGN_DIFFUSE_KL = Gauge('sovereign_diffuse_kl', 'Diffuse KL divergence')
SOVEREIGN_CACHE_ENTRIES = Gauge('sovereign_cache_entries', 'Cache entries count')
SOVEREIGN_ENTROPY_FLOOR = Gauge('sovereign_entropy_floor', 'Entropy floor')

# Trainer metrics
TRAINER_LOSS = Gauge('trainer_loss', 'Trainer loss')
TRAINER_BETA = Gauge('trainer_beta', 'Trainer beta')
TRAINER_T = Gauge('trainer_T', 'Trainer temperature')
TRAINER_KL_DIVERGENCE = Gauge('trainer_kl_divergence', 'Trainer KL divergence')

# Octonion heal loop metrics
OCTONION_HEAL_LOOP_STATUS = Gauge(
    'octonion_heal_loop_status', 
    'Octonion heal loop status (1 = healthy, 0 = healing)'
)

# New self-improving heal metrics (Entry 8367)
SOVEREIGN_OCTONION_HEAL_COUNT = Counter(
    'sovereign_octonion_heal_count', 
    'Total number of octonion heal events triggered'
)

SOVEREIGN_OCTONION_ADAPTIVE_SAMPLE_SIZE = Gauge(
    'sovereign_octonion_adaptive_sample_size',
    'Current adaptive sample size (3-14)'
)

SOVEREIGN_OCTONION_SUCCESS_RATE = Gauge(
    'sovereign_octonion_success_rate',
    'Rolling success rate of octonion healing (0-1)'
)

SOVEREIGN_OCTONION_HOT_PAIRS = Gauge(
    'sovereign_octonion_hot_pairs',
    'Number of hot pairs tracked by anomaly store'
)

# Dexterity index
SOVEREIGN_DEXTERITY_INDEX = Gauge(
    'sovereign_dexterity_index',
    'Overall dexterity index (0-1)'
)

SOVEREIGN_HEAL_RESILIENCE = Gauge(
    'sovereign_heal_resilience',
    'Heal resilience factor (0-1)'
)


class MetricsServer:
    """Prometheus metrics server."""
    
    def __init__(self, port=9090):
        self.port = port
        self.server_thread = None
    
    def start(self):
        """Start the metrics server."""
        self.server_thread = threading.Thread(
            target=start_http_server,
            args=(self.port,),
            daemon=True
        )
        self.server_thread.start()
        time.sleep(0.1)  # Give it time to start
    
    def stop(self):
        """Stop the metrics server."""
        # Prometheus server doesn't have a clean stop, but we can join the thread
        if self.server_thread:
            self.server_thread.join(timeout=1)


def update_octonion_heal_metrics(healer):
    """
    Update octonion heal loop metrics from the self-healer.
    
    Args:
        healer: OctonionSelfHealer instance
    """
    if healer:
        SOVEREIGN_OCTONION_ADAPTIVE_SAMPLE_SIZE.set(healer.get_adaptive_sample_size())
        SOVEREIGN_OCTONION_SUCCESS_RATE.set(healer.get_success_rate())
        SOVEREIGN_OCTONION_HOT_PAIRS.set(healer.get_hot_pairs_count())


def update_heal_loop_status(status):
    """
    Update the heal loop status gauge.
    
    Args:
        status: 1 for healthy, 0 for healing
    """
    OCTONION_HEAL_LOOP_STATUS.set(status)


def update_dexterity_metrics(dexterity, heal_resilience):
    """
    Update dexterity-related metrics.
    
    Args:
        dexterity: Overall dexterity index
        heal_resilience: Heal resilience factor
    """
    SOVEREIGN_DEXTERITY_INDEX.set(dexterity)
    SOVEREIGN_HEAL_RESILIENCE.set(heal_resilience)


# Initialize metrics server
metrics_server = MetricsServer()