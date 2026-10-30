# SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
# SPDX-License-Identifier: MIT

from fastapi import APIRouter

from app.config import settings

router = APIRouter()


@router.get("/pulse")
def pulse():
    return {
        "mcp": "port380",
        "filled": settings.MCP_FILLED,
        "port": settings.MCP_PORT,
        "phase_lock": settings.PHASE_LOCK,
        "tick": "6.49Hz",
    }
