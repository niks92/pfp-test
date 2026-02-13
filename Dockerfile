FROM python:3.11-slim AS base

WORKDIR /app

# Install dependencies in a separate layer for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ src/

# Non-root user for security
RUN useradd --create-home appuser
USER appuser

ENTRYPOINT ["python", "-m", "src.pipeline"]
