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
