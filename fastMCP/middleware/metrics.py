"""Metrics middleware for fastMCP."""

import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.time()
        response = await call_next(request)
        duration = time.time() - start
        # Log metrics (no external export)
        print(f"[metrics] {request.url.path} {duration:.3f}s")
        return response

metrics_middleware = MetricsMiddleware
