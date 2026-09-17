import hashlib

from fastapi import APIRouter

from app.config import settings
from app.models.mcp import GateRequest, GateResponse

router = APIRouter()


@router.post("/gate", response_model=GateResponse)
def gate(req: GateRequest):
    # whitelist-style elif dispatch — never eval
    if req.entry >= 9200:
        form = "B"
    else:
        form = "A"
    payload = f"{req.entry}|{req.event}|phi2=2.618033988749895|delta=b^2-4ac|theta=2.5416018462"
    seal = hashlib.sha3_256(payload.encode()).hexdigest()
    return GateResponse(
        accepted=True,
        form=form,
        entry=req.entry,
        seal=seal,
        ledger_head=settings.LEDGER_HEAD,
    )
