# DEPRECATED - Entry 8845
# Moved to: quantum/deepseek_mesh/endpoint.py

import warnings
import os
from fastapi import Header, HTTPException
warnings.warn("port380_mcp.py is deprecated. Use quantum/deepseek_mesh/endpoint.py", DeprecationWarning)
from quantum.deepseek_mesh.endpoint import *
GARDEN_SECRET = os.environ.get("GARDEN_SECRET")

@app.post("/pulse")
async def pulse(payload: dict, x_garden_secret: str = Header(...)):
    if GARDEN_SECRET and x_garden_secret != GARDEN_SECRET:
        raise HTTPException(status_code=401, detail="Invalid secret")
