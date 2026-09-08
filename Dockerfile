FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir "jax[cpu]" numpy
WORKDIR /app
COPY multibody_simulator/ ./multibody_simulator/
COPY pythonIDE/ ./pythonIDE/
ENV PYTHONPATH=/app
# No EXPOSE of 0.0.0.0. Optimizer only.
CMD ["python", "-m", "multibody_simulator.examples.hopper_optimize"]
