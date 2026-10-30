# SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
# SPDX-License-Identifier: MIT

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
