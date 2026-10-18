# ============================================================================
# AxiomicCoreness — canonical multi-stage image
#
# BUILD:
#   docker build -t axiomic-coreness:latest .
#
# RUN (FastAPI via port range):
#   docker run --rm -p 8080-8089:8080-8089 \
#     -e GARDEN_SECRET=... \
#     axiomic-coreness:latest
#
# RUN (port 380 MCP restart bridge, second process):
#   docker run --rm -p 380:380 \
#     -e GARDEN_SECRET=... \
#     axiomic-coreness:latest python3 port380_mcp.py
# ============================================================================

# ============================================================================
# STAGE 1 — PREBUILD GATE
# ============================================================================
# Golden identity returns 0. Bitten zeta bound is 2.366.
# Raw product 4.322935 is reported, not the exit code. No os._exit.
# ============================================================================
FROM python:3.12-slim AS prebuild
WORKDIR /prebuild
COPY scripts/pythonide_object.py /prebuild/pythonide_object.py
RUN python3 /prebuild/pythonide_object.py

# ============================================================================
# STAGE 2 — JAVA BUILD (produce target/classes and the jar)
# ============================================================================
# The Java sidecar is invoked from Python via subprocess:
#   java -cp target/classes com.fruitfly.brain.SovereignMain --chat ...
# This stage compiles it. Only target/ crosses to the runtime stage.
# ============================================================================
FROM maven:3.9-eclipse-temurin-17 AS java-builder

WORKDIR /build

# Copy POM first so Maven dependency cache survives source edits.
COPY pom.xml ./
COPY pom.yaml ./

# Resolve dependencies into the layer cache.
RUN mvn -B -q dependency:go-offline || true

# Copy Java sources and compile.
COPY src ./src
RUN mvn -B -q clean package -DskipTests

# Smoke: confirm the class file is present where Python will look.
RUN test -f target/classes/com/fruitfly/brain/SovereignMain.class \
    || (echo "SovereignMain.class missing" && exit 1)

# ============================================================================
# STAGE 3 — PYTHON RUNTIME (install requirements.txt + JDK)
# ============================================================================
FROM python:3.12-slim AS runtime

# ----------------------------------------------------------------------------
# SYSTEM RUNTIMES — JDK 17 required by the Java subprocess (Stage 2 output)
# ----------------------------------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
        openjdk-17-jre-headless \
        ca-certificates \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Sanity: the JVM is on PATH.
RUN java -version 2>&1 | head -1

# ----------------------------------------------------------------------------
# PYTHON ENVIRONMENT
# ----------------------------------------------------------------------------
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# ----------------------------------------------------------------------------
# PYTHON DEPS
# ----------------------------------------------------------------------------
COPY requirements.txt ./requirements.txt
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# ----------------------------------------------------------------------------
# APPLICATION CODE
# ----------------------------------------------------------------------------
# Includes app/, quantum/, tests/, scripts/, and specific entrypoints.
COPY app         ./app
COPY quantum     ./quantum
COPY tests       ./tests
COPY scripts     ./scripts
COPY port380_mcp.py ./port380_mcp.py
COPY luminara_slot.yaml ./luminara_slot.yaml

# ----------------------------------------------------------------------------
# JAVA ARTIFACTS
# ----------------------------------------------------------------------------
COPY --from=java-builder /build/target/classes ./target/classes
COPY --from=java-builder /build/target/sovereign-brain-1.0.0-SOVEREIGN.jar \
                         ./target/sovereign-brain-1.0.0-SOVEREIGN.jar

ENV SOVEREIGN_CP=/app/target/classes \
    JAVA_BIN=java \
    SOVEREIGN_TIMEOUT_S=180

# ----------------------------------------------------------------------------
# SECURITY & PORTS
# ----------------------------------------------------------------------------
# Creating user 1000 as required by the canonical spec
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER 1000

# 80    — canonical base port
# 380   — port380_mcp.py (garden-secret restart bridge)
# 8000  — FastAPI app (app.main:app) direct override
# 8080-8089 — uvicorn_range.py dynamic bind range
EXPOSE 80
EXPOSE 380
EXPOSE 8000
EXPOSE 8080-8089

# ----------------------------------------------------------------------------
# ENVIRONMENT & HEALTHCHECK
# ----------------------------------------------------------------------------
# BIND_HOST defaults to 0.0.0.0 in Docker so port publishing works out of the box.
# Local code defaults to 127.0.0.1, but containers require 0.0.0.0.
ENV BIND_HOST=0.0.0.0 \
    BIND_PORT_START=8080 \
    BIND_PORT_END=8089 \
    BIND_PORT=8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -fsS http://127.0.0.1:8000/healthz || curl -fsS http://127.0.0.1:8080/healthz || exit 1

# ----------------------------------------------------------------------------
# ENTRYPOINT
# ----------------------------------------------------------------------------
# Default: canonical range script. 
# Override for direct FastAPI (app.main:app) or port380_mcp.py.
CMD ["python3", "scripts/uvicorn_range.py"]
