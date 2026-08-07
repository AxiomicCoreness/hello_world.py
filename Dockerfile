FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY sovereign_engine.py .

ENV PHI=1.6180339887
ENV RHO_J=1330.0
ENV T_PHI=0.5983
ENV PHI_MINUS_709=6.7e-149

EXPOSE 8001

CMD ["python", "sovereign_engine.py"]