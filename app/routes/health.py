from fastapi import APIRouter

from app.config import settings

router = APIRouter()


@router.get("/health")
def health():
    return {
        "ok": True,
        "namespace": settings.NAMESPACE,
        "ledger_head": settings.LEDGER_HEAD,
        "seal": settings.SEAL,
    }
