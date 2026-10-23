# sovereign-irc-bridge

Autonomous WebSocket-to-TCP bridge **stubs** targeting **irc.abjects.net**,
with TeaVM UI wired to `games/teavm-rhythm` **debug-oracle**.

## Safety

- No real certs in git — `.env.example` only.
- **mTLS required at startup**: missing `IRC__MTLS_*` → `pydantic.ValidationError` (lifespan); no ghost-pass.
- **Live wire**: `WsTcpProxy` pumps WS↔TCP bytes over mTLS to `irc.abjects.net` once PEMs mount.
- Deploy workflow **skips green** when `secrets.KUBECONFIG` is empty.
- No dual-gate pytest files under this tree (no `test_*.py`).

## Layout

See `src/` (FastAPI + Pydantic), `deploy/k8s/`, `teavm-client/README.md`.

## Local

```bash
cd sovereign-irc-bridge
pip install -e .
# PEMs required (see .env.example) — app refuses to start without them
export IRC__MTLS_CERT_PATH=/etc/mtls/client.crt
export IRC__MTLS_KEY_PATH=/etc/mtls/client.key
export IRC__MTLS_CA_PATH=/etc/mtls/ca.crt
uvicorn src.main:app --host 0.0.0.0 --port 8080
```
## Debug-oracle chat commands

TeaVM panel `games/teavm-rhythm/.../debug-oracle` understands `/stokes`, `/flux`, `/mtls` — emits KaTeX from `docs/katex_stokes_mandala_9300_micro.*` via `hex_locks.json`. Host **irc.abjects.net**; live dial still fail-fast without mTLS.

