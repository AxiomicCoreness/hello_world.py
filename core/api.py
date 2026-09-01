#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
core/api.py

Sovereign FastAPI surface for DiffuseKLCache + Orchestrator health.
Entry 620 – Local smoke-test validated, now materialised on main.
Entry 623/624 – Prometheus instrumentation appended (no existing code removed).

Endpoints:
  GET  /test
  GET  /health
  GET  /diffuse_kl
  GET  /diffuse
  POST /add
  POST /objective
  GET  /metrics   (Prometheus)
  POST /token     (OAuth2)
  GET  /protected (OAuth2 protected)
"""

from typing import Dict, Any, Optional, List
import numpy as np
import os
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from jose import JWTError, jwt
from passlib.context import CryptContext

try:
    from core.diffuse_kl_cache import DiffuseKLCache
except ImportError:
    from .diffuse_kl_cache import DiffuseKLCache

# ------------------------------------------------------------------
# FastAPI application
# ------------------------------------------------------------------
app = FastAPI(
    title="Sovereign DiffuseKL API",
    version="1.0.0",
    description="FastAPI surface for DiffuseKLCache (Entry 620) + Prometheus (Entry 624) + OAuth2"
)

# Global cache instance
cache = DiffuseKLCache(M=1024, T=1.0, beta=0.1)

# ------------------------------------------------------------------
# OAuth2 configuration
# ------------------------------------------------------------------
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "sovereign_φ_secret_2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Fake user DB (replace with real user store)
fake_users_db = {
    "admin": {
        "username": "admin",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # "secret"
        "disabled": False,
    }
}

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return user_dict

def authenticate_user(db, username: str, password: str):
    user = get_user(db, username)
    if not user:
        return False
    if not verify_password(password, user["hashed_password"]):
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(fake_users_db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Example protected endpoint
@app.get("/protected")
async def protected_route(current_user: dict = Depends(get_current_user)):
    return {"message": f"Hello {current_user['username']}, you are authenticated!"}

# ------------------------------------------------------------------
# Prometheus instrumentation
# ------------------------------------------------------------------
try:
    from prometheus_client import Gauge, generate_latest, CONTENT_TYPE_LATEST
    from fastapi.responses import Response

    coherence_gauge = Gauge("sovereign_coherence", "Current coherence value")
    entropy_gauge = Gauge("sovereign_entropy_floor", "Entropy floor (symbolic)")
    diffuse_kl_gauge = Gauge("sovereign_diffuse_kl", "Current diffuse KL divergence")
    cache_entries_gauge = Gauge("sovereign_cache_entries", "Number of entries in DiffuseKLCache")

    coherence_gauge.set(1.0)
    entropy_gauge.set(0.0)
    diffuse_kl_gauge.set(0.0)
    cache_entries_gauge.set(0)

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False


class AddEntryRequest(BaseModel):
    entry: str
    embedding: List[float]
    entry_id: Optional[int] = None


class ObjectiveRequest(BaseModel):
    trajectory_log_prob: float = 0.0


@app.get("/test")
def test() -> Dict[str, Any]:
    return {
        "status": "ok",
        "message": "Sovereign FastAPI surface is live",
        "endpoints": ["/test", "/diffuse_kl", "/diffuse", "/health", "/add", "/objective", "/metrics", "/token", "/protected"],
        "coherence": 1.0,
        "phase_lock": 202.6,
        "prometheus": PROMETHEUS_AVAILABLE
    }


@app.get("/health")
def health() -> Dict[str, Any]:
    report = cache.health_report()
    if PROMETHEUS_AVAILABLE:
        try:
            coherence_gauge.set(1.0)
            diffuse_kl_gauge.set(cache.diffuse_kl())
            cache_entries_gauge.set(len(cache.ledger))
        except Exception:
            pass
    return {
        "status": "healthy",
        "service": "sovereign-diffuse-kl",
        "cache": report,
        "coherence": 1.0,
        "entropy_floor": "phi^-1418",
        "prometheus": PROMETHEUS_AVAILABLE
    }


@app.get("/diffuse_kl")
def diffuse_kl() -> Dict[str, Any]:
    try:
        value = cache.diffuse_kl()
        summary = cache.summary()
        if PROMETHEUS_AVAILABLE:
            diffuse_kl_gauge.set(value)
            cache_entries_gauge.set(summary.get("entries", 0))
        return {
            "diffuse_kl": value,
            "summary": summary,
            "status": "ok"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/diffuse")
def diffuse() -> Dict[str, Any]:
    kl = cache.diffuse_kl()
    summary = cache.summary()
    return {
        "status": "ok",
        "diffuse_kl": kl,
        "cache_size": summary["entries"],
        "top_bin": summary["top_bin"],
        "top_bin_mass": summary["top_bin_mass"],
        "M": summary["M"],
        "message": "Diffuse view derived from DiffuseKLCache"
    }


@app.post("/add")
def add_entry(req: AddEntryRequest) -> Dict[str, Any]:
    try:
        emb = np.array(req.embedding, dtype=np.float64)
        cache.add_entry(req.entry, emb, req.entry_id)
        if PROMETHEUS_AVAILABLE:
            cache_entries_gauge.set(len(cache.ledger))
            diffuse_kl_gauge.set(cache.diffuse_kl())
        return {
            "status": "added",
            "entry": req.entry,
            "bin": cache.hash_entry(req.entry),
            "current_entries": len(cache.ledger)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/objective")
def objective(req: ObjectiveRequest) -> Dict[str, Any]:
    try:
        value = cache.objective(req.trajectory_log_prob)
        return {
            "objective": value,
            "trajectory_log_prob": req.trajectory_log_prob,
            "diffuse_kl": cache.diffuse_kl(),
            "beta": cache.beta
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if PROMETHEUS_AVAILABLE:
    @app.get("/metrics")
    def metrics():
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    import uvicorn
    print("\u29c1\u2200 Starting Sovereign DiffuseKL FastAPI on http://0.0.0.0:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
