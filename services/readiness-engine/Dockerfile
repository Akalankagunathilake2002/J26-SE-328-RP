FROM python:3.12-slim

WORKDIR /service

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

EXPOSE 8010

CMD sh -c "uvicorn app.main:app --host 0.0.0.0 --port ${READINESS_ENGINE_PORT:-8010}"
