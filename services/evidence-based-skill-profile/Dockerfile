FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HF_HOME=/opt/huggingface \
    HF_HUB_DISABLE_XET=1

WORKDIR /service

COPY requirements.txt .
RUN pip install --no-cache-dir --timeout 120 --retries 10 -r requirements.txt

COPY . .

# AI models, skill index and evidence classifier are built into the image, so the service starts
# without downloads. Models already in docker-cache/hf (a copy of a local Hugging Face cache) are
# reused; missing ones are downloaded, and a missing index or classifier is built here.
RUN if [ -d docker-cache/hf ]; then mkdir -p "$HF_HOME/hub" && cp -r docker-cache/hf/. "$HF_HOME/hub/"; fi \
    && rm -rf docker-cache \
    && python -m scripts.prepare_models

ENV HF_HUB_OFFLINE=1

EXPOSE 8004

CMD sh -c "uvicorn app.main:app --host 0.0.0.0 --port ${EVIDENCE_SKILL_PROFILE_PORT:-8004}"
