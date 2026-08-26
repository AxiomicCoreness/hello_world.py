from fastapi import FastAPI, Request
from prometheus_client import make_asgi_app, Counter, Histogram, Gauge
import time
import math

PHI = (1.0 + math.sqrt(5.0)) / 2.0
SEAL_PREFIX = "∀∞φ²"

app = FastAPI(
    title="Port 380 / Layer 314 MCP Surface",
    description="Sovereign Ledger MCP-compatible endpoint surface with monitoring",
    version="1.0.0"
)

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP Requests",
    ["method", "endpoint", "http_status"]
)
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"]
)
REQUEST_IN_PROGRESS = Gauge(
    "http_requests_in_progress",
    "Number of in progress HTTP requests",
    ["method"]
)

metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

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

@app.get("/health")
async def health():
    return {"status": "healthy", "port": 380, "layer": 314}

@app.get("/status")
async def status():
    return {"status": "operational", "witness_chain": "UNBROKEN", "layer": "314", "port": 380}

@app.get("/380")
async def gate_380():
    return {"gate": "380", "layer": "314", "identity": "PRESERVED"}

@app.post("/gate")
async def post_gate(request: Request):
    try:
        payload = await request.json()
    except Exception:
        payload = {}
    return {"gate": "380", "layer": "314", "operation": "POST"}