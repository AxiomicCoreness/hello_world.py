#!/usr/bin/env python3
"""
🜁∀ SovereignConfig — Environment & API key management
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
        self.phi = 1.618033988749895
    
    @property
    def is_grok_ready(self) -> bool:
        return bool(self.grok_api_key)
    
    @property
    def is_mistral_ready(self) -> bool:
        return bool(self.mistral_api_key)
    
    def validate(self) -> Dict[str, bool]:
        """Check which services are configured."""
        return {
            "grok": self.is_grok_ready,
            "mistral": self.is_mistral_ready,
            "uphro_server": bool(self.uphro_server)
        }
