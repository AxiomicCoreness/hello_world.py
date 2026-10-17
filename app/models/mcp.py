"""
app/models/mcp.py

Pydantic models for the Port-380 MCP gate and pulse endpoints.

GateRequest   — POST body for /gate
GateResponse  — response shape returned by the gate handler
PulseResponse — response shape returned by /pulse

These are transport DTOs only. No ledger reads, no environment reads,
no I/O at import time.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

HEX64 = r"^[0-9a-f]{64}$"


class GateRequest(BaseModel):
    entry: int = Field(..., ge=0)
    event: str = Field(..., min_length=1)


class GateResponse(BaseModel):
    accepted: bool
    form: str = Field(..., pattern=r"^[AB]$")
    entry: int = Field(..., ge=0)
    seal: str = Field(..., pattern=HEX64)
    ledger_head: str


class PulseResponse(BaseModel):
    mcp: str
    filled: bool
    port: int = Field(..., ge=1, le=65535)
    phase_lock: float
    tick: str
