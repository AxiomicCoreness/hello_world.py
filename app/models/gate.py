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
    # Regime B event hash, same as the ledger verifier:
    # SHA3-256(domain + 0x00 + payload); LEDGER domain from 9281 on.
    domain = b"GARDEN.EVENT.v1.LEDGER" if req.entry >= 9281 else b"GARDEN.EVENT.v1"
    payload = f"{req.entry}|{req.event}|phi2=2.618033988749895|delta=b^2-4ac|theta=2.5416018462"
    seal = hashlib.new("sha3_256", domain + b"\x00" + payload.encode()).hexdigest()
    return GateResponse(
        accepted=True,
        form=form,
        entry=req.entry,
        seal=seal,
        ledger_head=settings.LEDGER_HEAD,
    )
