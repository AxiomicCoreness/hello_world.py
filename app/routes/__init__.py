"""Route package. Exports the FastAPI routers for app.main."""

from app.routes import gate, health, pulse, status, systems, tts, vision, vision_tts

ROUTERS = (
    health.router,
    status.router,
    gate.router,
    pulse.router,
    vision.router,
    systems.router,
    tts.router,
    vision_tts.router,
)

__all__ = [
    "gate",
    "health",
    "pulse",
    "status",
    "systems",
    "tts",
    "vision",
    "vision_tts",
    "ROUTERS",
]
