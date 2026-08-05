# Dockerfile – Gold Standard Sovereign FastAPI (Entry 623)
# Non-root, multi-stage, production-ready
FROM python:3.11-slim AS builder

WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.11-slim AS runtime

# Create non-root user
RUN addgroup --system --gid 1001 sovereign && \
    adduser --system --uid 1001 --gid 1001 --home /home/sovereign sovereign

WORKDIR /app

# Copy installed packages and application code
COPY --from=builder /root/.local /home/sovereign/.local
COPY core/ ./core/

# Environment
ENV PATH="/home/sovereign/.local/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    SOVEREIGN_MODE=production \
    PORT=8000

# Switch to non-root
USER 1001

EXPOSE 8000

# Health check (uses Python stdlib so no extra curl dependency)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')" || exit 1

CMD ["uvicorn", "core.api:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
