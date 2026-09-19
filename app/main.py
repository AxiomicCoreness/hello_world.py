from __future__ import annotations
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from app.config import settings
from app.routes import gate, health, pulse, status, systems, vision, tts, vision_tts
app = FastAPI(title="Sovereign Engine — FastAPI", version="5.2.0")
app.include_router(health.router)
app.include_router(status.router)
app.include_router(gate.router)
app.include_router(pulse.router)
app.include_router(vision.router)
app.include_router(systems.router)
app.include_router(tts.router)
app.include_router(vision_tts.router)
@app.get("/", response_class=HTMLResponse)
def root():
    return f"<html><body><h1>Sovereign Engine 5.2.0</h1><p>MCP Filled: {settings.MCP_FILLED}</p><ul><li><a href='/tts'>/tts</a></li><li><a href='/vision/tts'>/vision/tts</a></li></ul></body></html>"
