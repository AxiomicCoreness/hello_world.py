FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Core + MCP deps
COPY requirements.txt requirements-mcp.txt requirements-ci.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir -r requirements-mcp.txt \
    && pip install --no-cache-dir httpx>=0.27.0

# Application surface
COPY hello_world.py port380_mcp.py sovereign_engine.py ./
COPY deepseek/ ./deepseek/
COPY orchestrator/ ./orchestrator/
COPY contracts/ ./contracts/
COPY scripts/ ./scripts/

ENV PYTHONPATH=/app
ENV PHI=1.618033988749895
ENV LAYER=314
ENV PORT=8000

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# uvicorn entry (override CMD for SIMD or port380)
CMD ["sh", "-c", "uvicorn hello_world:app --host 0.0.0.0 --port ${PORT:-8000}"]
