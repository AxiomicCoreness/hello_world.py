from typing import Dict, Any, Optional
from clients.base_client import BaseClient
from .config import SovereignConfig

try:
    # Optional import of the DiffuseKLCache for ledger caching/health
    from core.diffuse_kl_cache import DiffuseKLCache
except Exception:
    DiffuseKLCache = None


class SovereignOrchestrator:
    def __init__(self, config: Optional[SovereignConfig] = None):
        self.config = config or SovereignConfig()
        self.clients: Dict[str, BaseClient] = {}
        # instantiate a DiffuseKLCache if available (non-critical)
        try:
            if DiffuseKLCache is not None:
                self.diffuse_cache = DiffuseKLCache()
            else:
                self.diffuse_cache = None
        except Exception:
            self.diffuse_cache = None

    @property
    def active_count(self) -> int:
        return len(self.clients)

    def register_client(self, name: str, client: BaseClient) -> None:
        self.clients[name] = client

    def health_report(self) -> Dict[str, Any]:
        """Full health check across all clients."""
        report = {
            "orchestrator": "🜁∀ active",
            "active_clients": self.active_count,
            "clients": {}
        }
        for name, client in self.clients.items():
            try:
                report["clients"][name] = client.health_check()
            except Exception as e:
                report["clients"][name] = {"status": "unreachable", "error": str(e)}
        # include cache health if available
        try:
            if getattr(self, "diffuse_cache", None) is not None:
                report["diffuse_cache"] = self.diffuse_cache.health_report()
            else:
                report["diffuse_cache"] = {"status": "unavailable"}
        except Exception as e:
            report["diffuse_cache"] = {"status": "error", "error": str(e)}
        return report
