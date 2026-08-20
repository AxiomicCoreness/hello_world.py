FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    unzip \
    jq \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements*.txt ./
RUN pip install --no-cache-dir -r requirements.txt || true
RUN pip install --no-cache-dir -r requirements-mcp.txt || true

# Copy application code
COPY . .

# Runtime env — PORT is injected by Render / K8s; default 8000
ENV PORT=8000 \
    GARDEN_SECRET="" \
    MCP_URL="" \
    PYTHONUNBUFFERED=1

# Metadata only (actual bind uses $PORT)
EXPOSE 8000

# Shell form so ${PORT} expands; conceptual Port 380 identity preserved in app
CMD ["sh", "-c", "exec uvicorn port380_mcp:app --host 0.0.0.0 --port ${PORT:-8000}"]
