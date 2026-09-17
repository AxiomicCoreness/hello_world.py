"""
app/models/gate.py

Pydantic models for the Port-380 MCP gate and pulse endpoints.

GateRequest  — POST body for /gate
GateResponse — response shape returned by the gate handler
PulseResponse — response shape returned by /pulse

These are transport DTOs only. No ledger reads, no environment reads,
no I/O at import time.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class GateRequest(BaseModel):
    entry: int = Field(..., ge=0)
    event: str = Field(..., min_length=1)


class GateResponse(BaseModel):
    accepted: bool
    form: str
    entry: int
    seal: str
    ledger_head: str


class PulseResponse(BaseModel):
    mcp: str
    filled: bool
    port: int
    phase_lock: float
