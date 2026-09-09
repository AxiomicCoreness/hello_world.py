"""Binder service — loopback policy enforcement."""

from fastMCP.constants import BIND_HOST, BIND_PORT
from fastMCP.exceptions import BindError

class BinderService:
    def __init__(self):
        self.host = BIND_HOST
        self.port = BIND_PORT

    def resolve(self, host: str = None, port: int = None):
        h = host or self.host
        p = port or self.port
        if h in {"0.0.0.0", "::", "[::]"}:
            raise BindError("wildcard host refused")
        if p != self.port:
            raise BindError(f"port must be {self.port}")
        return h, p
