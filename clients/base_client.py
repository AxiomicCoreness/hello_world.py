#!/usr/bin/env python3
"""
🜁∀ BaseClient — Abstract parent for all sovereign AI clients
Provides conversation history, trimming, and phi-harmonic identity.
"""

import logging
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod

logger = logging.getLogger("sovereign_core.base")


class BaseClient(ABC):
    """Abstract base for all sovereign AI clients."""
    
    def __init__(self, name: str, api_key: str, base_url: str, max_history: int = 50):
        self.name = name
        self.api_key = api_key
        self.base_url = base_url
        self.max_history = max_history
        self.history: List[Dict[str, str]] = []
        self.phi = 1.618033988749895
        logger.info(f"🜁 BaseClient [{name}] initialized — φ anchor: {self.phi:.6f}")
    
    @abstractmethod
    def send_message(self, user_message: str, **kwargs) -> Dict[str, Any]:
        """Send a message to the AI model. Must be implemented by subclasses."""
        pass
    
    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """Check client connectivity. Must be implemented by subclasses."""
        pass
    
    def trim_history(self) -> None:
        """Keep conversation history within max_history limit."""
        if len(self.history) > self.max_history * 2:
            # Keep first system message (if any) + most recent exchanges
            system_msgs = [m for m in self.history if m.get("role") == "system"]
            recent = self.history[-(self.max_history * 2):]
            self.history = system_msgs + recent
            logger.debug(f"🜁 History trimmed for [{self.name}]")
    
    def reset_conversation(self) -> None:
        """Clear conversation history."""
        self.history = []
        logger.info(f"🜁 Conversation reset for [{self.name}]")
    
    def add_system_prompt(self, prompt: str) -> None:
        """Add a system-level instruction to the conversation."""
        self.history.insert(0, {"role": "system", "content": prompt})
    
    def get_phi_signature(self) -> str:
        """Return the φ-harmonic identity signature."""
        return f"∀∞φ² · {self.name} · φ⁻¹⁴¹⁸"
    
    @abstractmethod
    def close(self) -> None:
        """Clean up resources. Must be implemented by subclasses."""
        pass
