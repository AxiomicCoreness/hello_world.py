# .container

Stdlib container app plus supervisor. No third-party dependencies.

## Files

    app.py          HTTP service: /healthz, /oidc_handover, /restart
    supervisor.py   process supervisor: respawn on exit 75
    Dockerfile      python:3.12-slim, non-root uid 10001, port 380

## Write surfaces

Four surfaces exist inside the container. Each has a defined writer and
a defined sink.

1. **Process state** — `/restart` sets `_state["restart_requested"]`,
   sends `SIGTERM` to self after 0.75s. Handler calls
   `server.shutdown()`. Main returns 75. Supervisor sees 75 and
   respawns. Any other exit code propagates up.
   Writer: HTTP client with `X-Garden-Secret`.
   Sink: supervisor loop.

2. **Filesystem state** — `STATE_DIR=/var/lib/sovereign`, owned by
   uid 10001. Mount a named volume or bind mount here so writes
   survive container restarts. Any file the app writes elsewhere
   in the image is lost on restart.
   Writer: the app process.
   Sink: mounted volume.

3. **Git state** — the container has no git binary by default. To
   push from inside, either:
   - mount the repo at `/repo` and add `git` to the image, with a
     deploy key at `/etc/sovereign/deploy_key` (mode 0600), or
   - perform git operations on the host/sidecar and let the
     container consume the result.
   Writer: git inside container OR host sidecar.
   Sink: remote git server.

4. **Logs** — `sys.stderr` from app and supervisor. Capture at the
   orchestrator: Docker `--log-driver`, compose `logging:`,
   k8s `stdout` capture. No files written for logs.

## Environment

Required:

    GARDEN_SECRET       auth for /oidc_handover, /restart, /380/restart

Optional:

    HOST                default 0.0.0.0
    PORT                default 380
    TLS_CERT            server certificate path
    TLS_KEY             server key path
    TLS_CA              CA for client-cert verification
    STATE_DIR           default /var/lib/sovereign

TLS is enabled only when all three of TLS_CERT / TLS_KEY / TLS_CA are
set. With all three present, the server requires and verifies a client
certificate (`ssl.CERT_REQUIRED`). With any missing, the server runs
plain HTTP and logs `tls: disabled`.

## Build

    docker build -f .container/Dockerfile -t sovereign-mcp:dev .

## Run

    docker run --rm -p 380:380 \
      -e GARDEN_SECRET=changeme \
      -v sovereign-state:/var/lib/sovereign \
      sovereign-mcp:dev

## Restart semantics

`POST /restart` returns 200, then the app exits 75 after 0.75s. The
supervisor respawns immediately (with backoff if the previous run was
short). If the orchestrator sends `SIGTERM`, the supervisor forwards
it to the child and exits 0 without respawn.

## Health check

    GET /healthz   ->   200 {"ok": true}

Unauthenticated. Works over TLS or plain HTTP on the same socket
mode as the app.
