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

# Bake the local embedding model into the image so EMBEDDING_PROVIDER=local works offline and
# startup ingestion doesn't stall on a download (~130 MB)
ENV HF_HOME=/opt/models FASTEMBED_CACHE_PATH=/opt/models/fastembed
RUN python -c "from fastembed import TextEmbedding; TextEmbedding('BAAI/bge-small-en-v1.5')"

# Copy application source code and data
COPY app/ ./app/
COPY models/ ./models/
COPY ingestion/ ./ingestion/
COPY data/ ./data/

HEALTHCHECK --interval=10s --timeout=5s --retries=3 \
  CMD sh -c "curl -f http://localhost:\${LEARNING_SERVICE_PORT:-\${SERVICE_PORT}}/health || exit 1"

CMD sh -c "uvicorn app.main:app --host 0.0.0.0 --port \${LEARNING_SERVICE_PORT:-\${SERVICE_PORT}}"

