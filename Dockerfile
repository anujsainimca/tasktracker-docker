# ---- Build stage ----
# Use a slim Python image to keep the final image small.
FROM python:3.11-slim AS base

# Prevents Python from writing .pyc files and enables unbuffered stdout/stderr
# so logs appear immediately in Docker/Kubernetes log streams.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies in a separate layer so Docker caches them unless
# requirements.txt changes — the most expensive step stays fast on rebuilds.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source last so code changes don't bust the dependency cache.
COPY . .

# ---- Runtime config ----
ENV FLASK_ENV=production \
    PORT=5000

EXPOSE 5000

# Run as a non-root user for defence-in-depth.
RUN adduser --disabled-password --gecos "" appuser
USER appuser

CMD ["python", "run.py"]
