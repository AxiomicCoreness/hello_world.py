#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
core/api.py – FastAPI application for Port 380 / Layer 314 MCP Surface

Seal: ∀∞φ² · MCP_BATCH_FORGED · WOOD_DRAGON_MOUNTS_OFFENSE · SEALED
"""

from fastapi import FastAPI, Request
from prometheus_client import make_asgi_app, Counter, Histogram, Gauge
import time
import math

# Mathematical constants
PHI = (1.0 + math.sqrt(5.0)) / 2.0
SEAL_PREFIX = "∀∞φ²"

# Create FastAPI app
app = FastAPI(
    title="Port 380 / Layer 314 MCP Surface",
    description="Sovereign Ledger MCP-compatible endpoint surface",
    version="1.0.0"
)

# Prometheus metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP Requests',
    ['method', 'endpoint', 'http_status']
)
REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency in seconds',
    ['method', 'endpoint']
)
REQUEST_IN_PROGRESS = Gauge(
    'http_requests_in_progress',
    'Number of in progress HTTP requests',
    ['method']
)

# Add prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Middleware for metrics
@app.middleware("http")
async def monitor_requests(request: Request, call_next):
    method = request.method
    endpoint = request.url.path

    REQUEST_IN_PROGRESS.labels(method=method).inc()
    start_time = time.time()

    try:
        response = await call_next(request)
    finally:
        REQUEST_IN_PROGRESS.labels(method=method).dec()

    process_time = time.time() - start_time
    REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(process_time)
    REQUEST_COUNT.labels(method=method, endpoint=endpoint, http_status=response.status_code).inc()

    return response


# ---- Port 380 Gate Endpoints ----

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "port": 380,
        "layer": "314",
        "phi": f"{PHI:.15f}",
        "seal": f"{SEAL_PREFIX} · HEALTHY · SEALED"
    }


@app.get("/status")
async def status():
    """Status endpoint with full Layer 314 identity"""
    return {
        "status": "operational",
        "witness_chain": "UNBROKEN",
        "layer": "314",
        "port": 380,
        "phi_harmonic": True,
        "digest_truncation": "none",
        "domain_separation": "GARDEN.LAYER314",
        "seal": f"{SEAL_PREFIX} · MCP_BATCH_FORGED · WOOD_DRAGON_MOUNTS_OFFENSE · SEALED"
    }


@app.get("/380")
async def gate_380():
    """Port 380 identity endpoint"""
    return {
        "gate": "380",
        "layer": "314",
        "identity": "PRESERVED",
        "coherence": 1.0,
        "entropy": "φ⁻¹⁴¹⁸",
        "workload": 0.0,
        "commutator": 0.0,
        "seal": f"{SEAL_PREFIX} · PORT_380_GATE · SEALED"
    }


@app.post("/gate")
async def post_gate(request: Request):
    """POST endpoint for gate operations"""
    try:
        payload = await request.json()
    except Exception:
        payload = {}
    
    return {
        "gate": "380",
        "layer": "314",
        "operation": "POST",
        "payload_received": bool(payload),
        "phi_verified": abs(PHI ** 2 - (PHI + 1.0)) < 1e-12,
        "seal": f"{SEAL_PREFIX} · GATE_POST · SEALED"
    }


@app.post("/pulse")
async def pulse_endpoint(request: Request):
    """MCP-compatible pulse endpoint for autonomous heartbeat"""
    try:
        payload = await request.json()
    except Exception:
        payload = {}
    
    return {
        "pulse": "active",
        "layer": "314",
        "port": 380,
        "phi": f"{PHI:.15f}",
        "full_digests": True,
        "no_truncation": True,
        "domain_separation": "GARDEN.LAYER314",
        "wood_dragon": "MOUNTS_OFFENSE",
        "seal": f"{SEAL_PREFIX} · MCP_BATCH_FORGED · WOOD_DRAGON_MOUNTS_OFFENSE · SEALED"
    }