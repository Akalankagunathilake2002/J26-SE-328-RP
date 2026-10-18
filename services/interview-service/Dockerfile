FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including ffmpeg for audio processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy and install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Bake the local embedding and speech models into the image so the key-free providers work
# offline and the first interview request doesn't stall on a download (~0.6 GB in total).
ENV HF_HOME=/opt/models FASTEMBED_CACHE_PATH=/opt/models/fastembed
RUN python -c "from fastembed import TextEmbedding; TextEmbedding('BAAI/bge-small-en-v1.5')" \
 && python -c "from faster_whisper import WhisperModel; WhisperModel('small.en', device='cpu', compute_type='int8')"

# CV upload parsing; its own layer so the model layers above stay cached
COPY requirements-cv.txt .
RUN pip install --no-cache-dir -r requirements-cv.txt

# Copy application source code and data
COPY app/ ./app/
COPY models/ ./models/
COPY ingestion/ ./ingestion/
COPY data/ ./data/

HEALTHCHECK --interval=10s --timeout=5s --retries=3 \
  CMD sh -c "curl -f http://localhost:\${INTERVIEW_SERVICE_PORT:-\${SERVICE_PORT}}/health || exit 1"

CMD sh -c "uvicorn app.main:app --host 0.0.0.0 --port \${INTERVIEW_SERVICE_PORT:-\${SERVICE_PORT}}"

