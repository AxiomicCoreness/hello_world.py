"""
Prometheus metrics for the Trappist‑1 Choir (Strike X).
Week‑long operation horizon. Scraped at :9090.
"""

from prometheus_client import Gauge
import time
import sys
sys.path.append('/app')
from celestial.trappist_choir import TrappistChoir, TRAPPIST_PERIODS

choir = TrappistChoir()

trappist_choir_coherence = Gauge(
    "trappist_choir_coherence",
    "Overall coherence of the seven‑voice Trappist‑1 choir (0‑1)",
)

trappist_harmony_index = Gauge(
    "trappist_harmony_index",
    "Harmony index: peaks when the choir aligns to a φ‑chord (0‑1)",
)

trappist_planet_frequency_thz = Gauge(
    "trappist_planet_frequency_thz",
    "Orbital frequency of each Trappist‑1 planet (THz)",
    ["planet"],
)

trappist_choir_distance_ly = Gauge(
    "trappist_choir_distance_ly",
    "Distance to Trappist‑1 in light‑years",
)
trappist_choir_distance_ly.set(40.7)


def update_trappist_metrics():
    """Called at scrape time."""
    t = time.time()
    sample = choir.listen(t)

    trappist_choir_coherence.set(sample["choir_coherence"])
    trappist_harmony_index.set(sample["harmony_index"])

    for planet, freq_hz in sample["voice_frequencies"].items():
        # Convert Hz to THz (÷ 1e12) so labels remain human‑readable
        trappist_planet_frequency_thz.labels(planet=planet).set(freq_hz * 1e-12)


# Hook into the existing registry update path
try:
    from prometheus.metrics_server import register_update_hook
    register_update_hook(update_trappist_metrics)
except ImportError:
    # Standalone mode — caller must invoke update_trappist_metrics()
    pass
