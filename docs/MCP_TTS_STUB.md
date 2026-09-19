# MCP · Vision TTS · FastAPI TTS stubs

| Surface | Path | Filled |
|---------|------|--------|
| MCP | `fastMCP/routes/mcp.py`, `port380_mcp.py` | **False** |
| FastAPI TTS | `app/routes/tts.py` — GET/POST `/tts` | **False** (no audio) |
| Vision TTS | `app/routes/vision_tts.py` — GET `/vision/tts` | **False** |

Bind policy for local probes: `127.0.0.1` only on dual ASGI / fastMCP gearbox.
Pod-internal FastAPI may use cluster DNS; do not advertise `0.0.0.0` as public.

Merge engine does not rewrite sealed ledger bodies.
