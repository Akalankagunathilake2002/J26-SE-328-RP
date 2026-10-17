FROM python:3.12-slim

WORKDIR /service

COPY pyproject.toml README.md ./
COPY app ./app
COPY config ./config
RUN pip install --no-cache-dir -e .

EXPOSE 8003

# Serves the Market Pulse API. docker-compose mounts data/processed read-only; collection runs on the host.
CMD sh -c "uvicorn app.main:app --host 0.0.0.0 --port ${JOB_MARKET_INTELLIGENCE_PORT:-8003}"
