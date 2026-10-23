# Multi-stage: Python bridge + TeaVM debug-oracle static assets (no live certs).
FROM python:3.12-slim AS bridge
WORKDIR /app
COPY sovereign-irc-bridge/pyproject.toml /app/sovereign-irc-bridge/
COPY sovereign-irc-bridge/src /app/sovereign-irc-bridge/src
# TeaVM client surface: existing debug-oracle (not a duplicate teavm-client build)
COPY games/teavm-rhythm/src/main/webapp/debug-oracle /app/static/debug-oracle
RUN pip install --no-cache-dir /app/sovereign-irc-bridge
ENV PYTHONPATH=/app/sovereign-irc-bridge
WORKDIR /app/sovereign-irc-bridge
# Rewrite static mount path expectation via env for container layout
ENV BRIDGE_STATIC_DEBUG_ORACLE=/app/static/debug-oracle
EXPOSE 8080
CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]
