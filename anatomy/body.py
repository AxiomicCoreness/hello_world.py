"""anatomy/body.py — loopback bind, no wildcard, resource limits.

Bind surface for organ services: only loopback, never 0.0.0.0/::.
Enforces conservative resource ceilings. No MCP writes.
"""

import resource
import socket

ALLOWED_HOSTS = {"127.0.0.1", "::1", "localhost"}
MAX_FD_SOFT = 256
MAX_MEM_MB = 512


def assert_loopback(host: str) -> None:
    if host not in ALLOWED_HOSTS:
        raise ValueError(f"non-loopback bind refused: {host!r}")


def bind_loopback(port: int, host: str = "127.0.0.1") -> socket.socket:
    """Bind a loopback-only socket. Never a wildcard address."""
    assert_loopback(host)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((host, port))
    return sock


def apply_resource_limits(max_fd: int = MAX_FD_SOFT, max_mem_mb: int = MAX_MEM_MB) -> None:
    resource.setrlimit(resource.RLIMIT_NOFILE, (max_fd, max_fd))
    mem = max_mem_mb * 1024 * 1024
    try:
        resource.setrlimit(resource.RLIMIT_AS, (mem, mem))
    except (ValueError, OSError):
        pass  # RLIMIT_AS unsupported on some platforms; NOFILE still enforced.


if __name__ == "__main__":
    apply_resource_limits()
    print("body: loopback-only policy active, resource limits applied")
