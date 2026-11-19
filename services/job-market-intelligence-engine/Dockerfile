FROM python:3.12-slim AS api

WORKDIR /service

COPY pyproject.toml README.md ./
COPY app ./app
COPY config ./config
RUN pip install --no-cache-dir -e .

EXPOSE 8003

# Serves the Market Pulse API. docker-compose mounts data/processed read-only.
CMD sh -c "uvicorn app.main:app --host 0.0.0.0 --port ${JOB_MARKET_INTELLIGENCE_PORT:-8003}"

# Step 8: the daily sync (the opt-in job-market-sync service in docker-compose). Adds Tesseract to
# read the flyers and the PostgreSQL driver to load job_market_db.
FROM api AS sync

RUN apt-get update \
    && apt-get install -y --no-install-recommends tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir -e ".[db]"

CMD ["python", "-m", "app.collectors.schedule"]
