# Dockerfile for Sovereign Garden
# ==============================
# Build: docker build -t sovereign-garden .
# Run:   docker run -p 8000:8000 --restart unless-stopped sovereign-garden

FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PIP_NO_CACHE_DIR 1

# Install system dependencies (base)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create .env file from environment variables
RUN echo "GROK_API_KEY=${GROK_API_KEY:-}" > .env && \
    echo "MISTRAL_API_KEY=${MISTRAL_API_KEY:-}" >> .env && \
    echo "UPHRO_SERVER_URL=${UPHRO_SERVER_URL:-http://localhost:8081/api/status}" >> .env

# Expose port
EXPOSE 8000

# ============================================================
# ⬇️  APPENDED LINES (no lines above are removed)
# ============================================================

# Install additional system dependencies for OAuth2 / JWT (cryptography)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Create a non‑root user for running the application (security best practice)
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Healthcheck – verifies that the /health endpoint responds
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# OAuth2 configuration (override via -e or .env file)
ENV OAUTH2_CLIENT_ID=sovereign_garden \
    OAUTH2_CLIENT_SECRET=change_me \
    OAUTH2_TOKEN_URL=/token \
    JWT_SECRET_KEY=sovereign_φ_secret_2026

# Command to run the application – using the core auto‑restart entry point (Entry 0252)
CMD ["python", "-O", "core"]
