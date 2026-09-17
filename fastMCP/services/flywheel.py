"""Flywheel service — re-exports ASGI app."""

from fastMCP.gearbox import app

class FlywheelService:
    app = app
