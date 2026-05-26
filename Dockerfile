# CVPilot production image (API + worker share this).
# Process selected via fly.api.toml / fly.worker.toml [processes].
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/app

WORKDIR /app

# System deps for psycopg + cryptography.
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps first for layer cache.
COPY requirements.txt ./
RUN pip install -r requirements.txt

# App code.
COPY . .

EXPOSE 8080

# Default command; overridden by [processes] in fly.*.toml.
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8080"]
