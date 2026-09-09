"""Type definitions for fastMCP."""

from typing import TypedDict, Optional, List, Dict, Any

class Envelope(TypedDict, total=False):
    """Envelope structure for phi-harmonic state."""
    phi: float
    state: str
    coherence: float
    timestamp: str

class BindConfig(TypedDict):
    """Bind configuration."""
    host: str
    port: int
    filled: bool
