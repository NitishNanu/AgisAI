# ============================================================
# AegisAI Backend — Multi-Stage Production Dockerfile
# Python 3.10-slim | Non-root user | Security hardened
# ============================================================

FROM python:3.10-slim AS base

# Prevent Python from writing .pyc files and enable unbuffered stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies for psycopg2 / GeoAlchemy2 / PostGIS
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    libgeos-dev \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*


# ============================================================
# Dependency builder stage
# ============================================================
FROM base AS builder

WORKDIR /build

COPY requirements.txt .
RUN pip install --prefix=/install --no-cache-dir -r requirements.txt


# ============================================================
# Final production image
# ============================================================
FROM base AS production

# Create non-root application user
RUN groupadd --gid 1001 aegis && \
    useradd --uid 1001 --gid aegis --no-create-home --shell /bin/bash aegis

WORKDIR /app

# Copy installed packages from builder stage
COPY --from=builder /install /usr/local

# Copy application source code
COPY --chown=aegis:aegis . .

# Switch to non-root user
USER aegis

EXPOSE 8000

# Health check — hits the /api/v1/health endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Run application via uvicorn with production settings
CMD ["uvicorn", "app.main:app", \
    "--host", "0.0.0.0", \
    "--port", "8000", \
    "--workers", "4", \
    "--loop", "uvloop", \
    "--http", "httptools", \
    "--access-log", \
    "--log-level", "info"]
