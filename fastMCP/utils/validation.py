"""Validation utilities."""

from fastMCP.constants import BIND_HOST, BIND_PORT

def validate_bind(host: str, port: int) -> bool:
    """Validate bind configuration."""
    return host == BIND_HOST and port == BIND_PORT
