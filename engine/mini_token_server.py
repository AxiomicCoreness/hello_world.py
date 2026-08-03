from fastapi import FastAPI
from fastapi.responses import JSONResponse
import secrets, time
app = FastAPI()
@app.get("/oauth/health")
def health():
    return {"ok": True}
@app.post("/oauth/token")
async def token(body: dict | None = None):
    return JSONResponse({
        "access_token": secrets.token_hex(16),
        "token_type": "bearer",
        "expires_in": 3600,
        "iat": int(time.time()),
    })
