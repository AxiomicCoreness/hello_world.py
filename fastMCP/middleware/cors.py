"""CORS middleware for fastMCP."""

from starlette.middleware.cors import CORSMiddleware

def cors_middleware(app):
    """Add CORS middleware with loopback-only policy."""
    return CORSMiddleware(
        app,
        allow_origins=["http://127.0.0.1:8024"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
