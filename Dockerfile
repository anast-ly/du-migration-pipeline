# syntax=docker/dockerfile:1

# --- Base image -------------------------------------------------------------
# slim keeps the image small; psycopg2-binary ships its own libpq so we need
# no apt build dependencies.
FROM python:3.11-slim

# PYTHONUNBUFFERED makes logs stream in real time (important for Cloud Run /
# docker-compose log visibility); no .pyc clutter in the image.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# --- Install the package ----------------------------------------------------
# Copy only what's needed to build/install, so the image stays clean.
COPY pyproject.toml ./
COPY src/ ./src/
RUN pip install --no-cache-dir .

# --- Run as a non-root user -------------------------------------------------
RUN useradd --create-home --uid 1000 appuser
USER appuser

# The migration job runs to completion and exits (batch job, not a service).
ENTRYPOINT ["python", "-m", "migration"]
