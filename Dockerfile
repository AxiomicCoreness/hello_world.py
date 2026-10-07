# Prebuild gate: golden identity returns 0. Bitten zeta bound is 2.366.
# Raw product 4.322935 is reported, not the exit code. No os._exit.
FROM python:3.12-slim AS prebuild
WORKDIR /prebuild
COPY scripts/pythonide_object.py /prebuild/pythonide_object.py
RUN python3 /prebuild/pythonide_object.py

FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
COPY scripts/pythonide_object.py ./scripts/pythonide_object.py
EXPOSE 80
ENV BIND_HOST=0.0.0.0 BIND_PORT=80
USER 1000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]

