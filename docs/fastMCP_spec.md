# fastMCP spec

Modular name-seal over `fastapi_flywheel_gearbox:app`.

- Bind: `127.0.0.1:8024` only. Wildcard refused.
- MCP: `FILLED=False`. `/mcp` is a status stub.
- One ASGI object. No second daemon.
- Control-layer deps: `requirements-control.txt`.
- Slices under `requirements/` do not replace the control file.

Dispatch:

```bash
uvicorn fastMCP.gearbox:app --host 127.0.0.1 --port 8024
python -m fastMCP
```
