# DeepSeek Mesh Quadrant - Entry 8844/8845 + harness lattice
# DeepSeek client, MCP endpoint, DeepSeek-only adapter (deepseek_http)

from . import client, endpoint, dsh_adapter
from .dsh_adapter import (
    MODE_DEEPSEEK_HTTP,
    MODE_DSH,
    MODE_OFFLINE,
    AdapterResult,
    complete,
    deepseek_http_complete,
    dsh_complete,
    offline_complete,
    probe,
)
from .client import chat, chat_http, echo, status

__all__ = [
    "client",
    "endpoint",
    "dsh_adapter",
    # mode labels
    "MODE_OFFLINE",
    "MODE_DEEPSEEK_HTTP",
    "MODE_DSH",
    # adapter surface
    "AdapterResult",
    "complete",
    "deepseek_http_complete",
    "dsh_complete",
    "offline_complete",
    "probe",
    # thin client
    "chat",
    "chat_http",
    "echo",
    "status",
]
