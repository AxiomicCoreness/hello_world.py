from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from app.config import settings
from app.routes import ROUTERS

app = FastAPI(title="Sovereign Engine — FastAPI", version="5.2.0")

for router in ROUTERS:
    app.include_router(router)


@app.get("/", response_class=HTMLResponse)
def root():
    return f"""
    <!DOCTYPE html>
    <html>
      <head>
        <title>🔬∀ Sovereign Engine</title>
        <style>
          body {{ background:#0a0e1a; color:#c9d1d9; font-family:Consolas,monospace; padding:2rem; }}
          .locked {{ color:#7fffd4; }}
          .panel  {{ border:2px solid #7fffd4; border-radius:6px; padding:1rem; margin:1rem 0; }}
        </style>
      </head>
      <body>
        <h1 class="locked">🔬∀ SOVEREIGN ENGINE — START HERE</h1>
        <div class="panel">
          <p>Namespace:   {settings.NAMESPACE}</p>
          <p>Ledger Head: {settings.LEDGER_HEAD}</p>
          <p>Phase Lock:  {settings.PHASE_LOCK}°</p>
          <p>MCP Filled:  {settings.MCP_FILLED}</p>
          <p>Bind:        0.0.0.0:{settings.BIND_PORT_START}-{settings.BIND_PORT_END}</p>
          <p>Version:     5.2.0 — vision + TTS stubs + systems soft-gate</p>
        </div>
        <div class="panel">
          <p>Endpoints:</p>
          <ul>
            <li><a href="/health">/health</a></li>
            <li><a href="/status">/status</a></li>
            <li><a href="/vision">/vision</a></li>
            <li><a href="/vision/tts">/vision/tts</a></li>
            <li><a href="/tts">/tts</a></li>
            <li><a href="/systems">/systems</a></li>
            <li><a href="/docs">/docs</a></li>
            <li>POST /gate</li>
            <li>GET  /pulse</li>
          </ul>
        </div>
      </body>
    </html>
    """
