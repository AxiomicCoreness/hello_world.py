from __future__ import annotations

import os
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routes import ROUTERS

app = FastAPI(title="Sovereign Engine — FastAPI", version="5.2.0")

# ==============================================================================
# SECURITY HARDENING: CORS VULNERABILITY PATCH
# ==============================================================================
# Fetch explicit allowlist from environment (comma-separated).
# Prevents dynamic Origin reflection and wildcard "*" bleeding under load.
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "https://axiomiccoreness.local").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in ALLOWED_ORIGINS if o.strip()],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    # Explicit headers only — no wildcard with credentials.
    allow_headers=["Content-Type", "Authorization", "X-Garden-Secret", "X-Ledger-Head"],
    expose_headers=["X-Ledger-Head"],
    max_age=3600,  # Cache preflight for 1 hour to absorb spikes
)
# ==============================================================================

for router in ROUTERS:
    app.include_router(router)


@app.get("/", response_class=HTMLResponse)
def root():
    # F-string correctly escapes CSS braces as {{ and }}
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
