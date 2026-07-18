#!/usr/bin/env python3
"""
🜁∀ SovereignOrchestrator — Multi-agent coordination hub
Routes messages between Grok and Mistral with φ-harmonic load balancing.
"""

import logging
from typing import Dict, Any, Optional
from clients.base_client import BaseClient
from .config import SovereignConfig

logger = logging.getLogger("sovereign_core.orchestrator")


class SovereignOrchestrator:
    """Multi-agent orchestrator with φ-weighted routing."""
    
    def __init__(self, config: Optional[SovereignConfig] = None):
        self.config = config or SovereignConfig()
        self.clients: Dict[str, BaseClient] = {}
        
        # Initialize available clients (placeholder for Grok/Mistral)
        # if self.config.is_grok_ready:
        #     from clients.grok_client import GrokClient
        #     self.clients["grok"] = GrokClient(self.config.grok_api_key)
        # if self.config.is_mistral_ready:
        #     from clients.mistral_client import MistralClient
        #     self.clients["mistral"] = MistralClient(self.config.mistral_api_key)
        
        self.active_count = len(self.clients)
        logger.info(f"🜁 Orchestrator initialized — {self.active_count} clients active")
    
    def send_to(self, agent: str, message: str, **kwargs) -> Dict[str, Any]:
        """Send a message to a specific agent."""
        if agent not in self.clients:
            raise ValueError(f"Agent '{agent}' not available. Active: {list(self.clients.keys())}")
        return self.clients[agent].send_message(message, **kwargs)
    
    def broadcast(self, message: str, **kwargs) -> Dict[str, Dict[str, Any]]:
        """Send the same message to all active agents."""
        results = {}
        for name, client in self.clients.items():
            try:
                results[name] = client.send_message(message, **kwargs)
            except Exception as e:
                results[name] = {"error": str(e)}
        return results
    
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
        return report
    
    def close_all(self):
        """Gracefully close all client connections."""
        for name, client in self.clients.items():
            try:
                client.close()
                logger.info(f"🜁 {name} client closed")
            except Exception as e:
                logger.warning(f"🜁 Error closing {name}: {e}")
        logger.info("🜁 All clients closed. Garden at rest.")
