"""Prometheus Metrics"""
from prometheus_client import start_http_server, Gauge
sovereign_coherence = Gauge("sovereign_coherence", "Garden coherence")
sovereign_coherence.set(0.999999999999999)
start_http_server(9090)
print("Metrics at :9090")