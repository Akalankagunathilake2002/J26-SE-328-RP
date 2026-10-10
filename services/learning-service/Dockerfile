FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code and data
COPY app/ ./app/
COPY ingestion/ ./ingestion/
COPY data/ ./data/

HEALTHCHECK --interval=10s --timeout=5s --retries=3 \
  CMD sh -c "curl -f http://localhost:\${LEARNING_SERVICE_PORT:-\${SERVICE_PORT}}/health || exit 1"

CMD sh -c "uvicorn app.main:app --host 0.0.0.0 --port \${LEARNING_SERVICE_PORT:-\${SERVICE_PORT}}"

