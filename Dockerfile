FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r /tmp/requirements.txt
WORKDIR /app
COPY pythonIDE/ ./pythonIDE/
COPY multibody_simulator/ ./multibody_simulator/
ENV PYTHONPATH=/app
CMD ["python", "-m", "pythonIDE.hopper_optimize"]
