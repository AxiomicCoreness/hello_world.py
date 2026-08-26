#!/usr/bin/env python3
"""
🜁∀ SovereignConfig — Environment & API Key Management
"""

import os
from typing import Dict
from dotenv import load_dotenv

load_dotenv()


class SovereignConfig:
    """Sovereign configuration manager with φ-harmonic defaults."""

    def __init__(self):
        self.grok_api_key = os.getenv("GROK_API_KEY")
        self.mistral_api_key = os.getenv("MISTRAL_API_KEY")
        self.uphro_server = os.getenv("UPHRO_SERVER_URL", "http://localhost:8081/api/status")
        self.phi = 1.618033988749895  # Golden ratio constant

    @property
    def is_grok_ready(self) -> bool:
        """Check if Grok API key is configured."""
        return bool(self.grok_api_key)

    @property
    def is_mistral_ready(self) -> bool:
        """Check if Mistral API key is configured."""
        return bool(self.mistral_api_key)

    def validate(self) -> Dict[str, bool]:
        """Check which services are configured.

        Returns:
            Dict[str, bool]: Dictionary indicating readiness of each service.
        """
        return {
            "grok": self.is_grok_ready,
            "mistral": self.is_mistral_ready,
            "uphro_server": bool(self.uphro_server)
        }

    def get_lindblad_equation(self) -> str:
        """Return the Lindblad master equation for quantum state evolution."""
        return r"dρ/dt = -i[H,ρ] + Σ_k (L_k ρ L_k† - ½{L_k†L_k, ρ})"
