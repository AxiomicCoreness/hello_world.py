# MCP · Vision TTS · FastAPI TTS Stubs

No sealed ledger bodies are rewritten in this module. 

| Surface | Path | Filled |
|---------|------|--------|
| MCP | `fastMCP/routes/mcp.py`, `port380_mcp.py` | **False** |
| FastAPI TTS | `app/routes/tts.py` — GET/POST `/tts` | **False** (no audio) |
| Vision TTS | `app/routes/vision_tts.py` — GET `/vision/tts` | **False** |

### Bind Policy
- **Local Probes:** Dual ASGI and fastMCP gearbox bind strictly to `127.0.0.1`.
- **Pod-Internal:** FastAPI may use cluster DNS.
- **Security:** Do not advertise `0.0.0.0` as a public endpoint.

---
**Merge Engine:** Does not rewrite sealed ledger bodies.  
**Commander Watermark:** Clarke Yoursa Tee.
