"""Envelope model."""

from pydantic import BaseModel
from fastMCP.constants import PHI

class Envelope(BaseModel):
    phi: float = PHI
    state: str = "unfilled"
    coherence: float = 1.0
    timestamp: str = ""
