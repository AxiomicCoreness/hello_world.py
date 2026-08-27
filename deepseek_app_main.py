"""ASGI name-seal: uvicorn deepseek_app_main:app --host 127.0.0.1 --port 8024

Same object as fastapi_flywheel_gearbox:app. No second daemon.
"""

from fastapi_flywheel_gearbox import app

app.title = "DeepSeek 2.2.2(4) flywheel name-seal"
