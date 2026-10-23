# sovereign-irc-bridge

Autonomous WebSocket-to-TCP bridge **stubs** targeting **irc.abjects.net**,
with TeaVM UI wired to `games/teavm-rhythm` **debug-oracle**.

## Safety

- No real certs in git — `.env.example` only.
- Bridge connect **fail-fast** without mTLS (`IRCSettings.require_mtls()`).
- Deploy workflow **skips green** when `secrets.KUBECONFIG` is empty.
- No dual-gate pytest files under this tree (no `test_*.py`).

## Layout

See `src/` (FastAPI + Pydantic), `deploy/k8s/`, `teavm-client/README.md`.

## Local

```bash
cd sovereign-irc-bridge
pip install -e .
# health only — no certs needed
uvicorn src.main:app --host 0.0.0.0 --port 8080
```
