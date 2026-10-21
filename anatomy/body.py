"""anatomy/body.py — loopback bind, no wildcard, resource limits.

Bind surface for organ services: only loopback, never 0.0.0.0/::.
Enforces conservative resource ceilings. No MCP writes.
"""

import socket

# Fallback for non-POSIX systems (like Windows) or restricted CI sandboxes
try:
    import resource
    HAS_RESOURCE = True
except ImportError:
    HAS_RESOURCE = False

ALLOWED_HOSTS = {"127.0.0.1", "::1", "localhost"}
MAX_FD_SOFT = 256
MAX_MEM_MB = 512


def assert_loopback(host: str) -> None:
    """Ensure the bind address is strictly loopback."""
    if host not in ALLOWED_HOSTS:
        raise ValueError(f"non-loopback bind refused: {host!r}")


def bind_loopback(port: int, host: str = "127.0.0.1") -> socket.socket:
    """Bind a loopback-only socket. Never a wildcard address."""
    assert_loopback(host)
    
    # Use AF_INET6 if the host is an IPv6 loopback
    family = socket.AF_INET6 if host == "::1" else socket.AF_INET
    
    sock = socket.socket(family, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((host, port))
    return sock


def apply_resource_limits(max_fd: int = MAX_FD_SOFT, max_mem_mb: int = MAX_MEM_MB) -> None:
    """Apply resource limits, ignoring unsupported platforms or permission errors."""
    if not HAS_RESOURCE:
        print("⚠️ 'resource' module not available (Windows or restricted sandbox). Skipping rlimits.")
        return

    # 1. Enforce File Descriptors (NOFILE)
    try:
        resource.setrlimit(resource.RLIMIT_NOFILE, (max_fd, max_fd))
    except (ValueError, OSError, PermissionError) as e:
        print(f"⚠️ Could not set RLIMIT_NOFILE (may require root): {e}")

    # 2. Enforce Virtual Memory (AS)
    mem = max_mem_mb * 1024 * 1024
    try:
        resource.setrlimit(resource.RLIMIT_AS, (mem, mem))
    except (ValueError, OSError, PermissionError) as e:
        # RLIMIT_AS is often unsupported on macOS or blocked in CI
        print(f"⚠️ Could not set RLIMIT_AS: {e}")


if __name__ == "__main__":
    apply_resource_limits()
    print("body: loopback-only policy active, resource limits applied")
