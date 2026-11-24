FROM python:3.12-slim AS api

WORKDIR /service

COPY pyproject.toml README.md ./
COPY app ./app
COPY config ./config
# [db]: the PostgreSQL driver, so the API can build Market Pulse from the database.
RUN pip install --no-cache-dir -e ".[db]"

EXPOSE 8003

# Serves the Market Pulse API: from the database when SKILLBRIDGE_DATABASE_URL is set, otherwise from
# data/processed/skill_profile.json (docker-compose mounts data/processed read-only).
CMD sh -c "uvicorn app.main:app --host 0.0.0.0 --port ${JOB_MARKET_INTELLIGENCE_PORT:-8003}"

# Step 8: the daily sync (the opt-in job-market-sync service in docker-compose). Adds Tesseract to
# read the flyers (the PostgreSQL driver is already in the api stage).
FROM api AS sync

RUN apt-get update \
    && apt-get install -y --no-install-recommends tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

CMD ["python", "-m", "app.collectors.schedule"]
