FROM python:3.11-slim

WORKDIR /app

# System deps for numpy/xgboost
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# App code
COPY . .

# Bootstrap script: generates data, trains models, seeds DB if artefacts absent.
# Runs at container start-up so a fresh deployment is one command.
RUN chmod +x scripts/entrypoint.sh 2>/dev/null || true

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["sh", "-c", "python -m scripts.bootstrap && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
