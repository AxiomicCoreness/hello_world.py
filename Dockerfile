# Port 380 MCP Service
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY port380_mcp.py .

EXPOSE 380

CMD ["python", "port380_mcp.py"]