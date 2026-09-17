"""Authentication middleware for fastMCP."""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # No secrets — loopback only
        response = await call_next(request)
        return response

auth_middleware = AuthMiddleware
