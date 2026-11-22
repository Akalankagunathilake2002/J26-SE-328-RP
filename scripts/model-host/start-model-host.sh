#!/bin/zsh
# Serves this Mac's models to a hosted SkillBridge server: Gemma (and the avatar engine, if it is running)
# behind model_gateway.py, published through an ngrok tunnel. Prints the settings for the server.
#
#   scripts/model-host/start-model-host.sh            # Gemma + avatar engine + gateway + tunnel
#   NO_AVATAR=1 scripts/model-host/start-model-host.sh     # without the avatar (saves about 2.2 GB)
#
# Ctrl-C stops everything it started.
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
HUGGINGBAY="${HUGGINGBAY:-/Volumes/Dilmith Ext/Huggingbay}"
MODEL="${LLM_MODEL:-$HUGGINGBAY/models/gemma-4-e4b-4bit-mlx}"
KEY_FILE="$HOME/.skillbridge-local/model-host.key"
LOGS="$HOME/.skillbridge-local/logs"
mkdir -p "$LOGS"

# The access key the server sends (MODEL_HOST_KEY); kept outside the repo, made once
if [[ ! -s "$KEY_FILE" ]]; then
  python3 -c "import secrets; print(secrets.token_urlsafe(32))" > "$KEY_FILE"
  chmod 600 "$KEY_FILE"
fi
export MODEL_HOST_KEY="$(cat "$KEY_FILE")"

pids=()
trap 'kill ${pids[@]} 2>/dev/null; echo "Stopped."' EXIT INT TERM

# Keep the Mac awake while serving: if it sleeps, the tunnel drops and the site loses its LLM
caffeinate -ims -w $$ &
pids+=($!)

wait_for() {  # port, name
  for i in {1..120}; do lsof -iTCP:$1 -sTCP:LISTEN >/dev/null 2>&1 && return 0; sleep 1; done
  echo "$2 did not start (see $LOGS)"; exit 1
}

# Gemma. --prompt-cache-size keeps the KV cache of recent prompts, so the interviewer's and Skillaro's
# repeated instructions aren't re-processed on every call; --decode-concurrency 2 lets a prefetched
# interview question generate alongside the current request instead of queueing behind it.
if ! lsof -iTCP:8082 -sTCP:LISTEN >/dev/null 2>&1; then
  "$HUGGINGBAY/.venv/bin/mlx_lm.server" --model "$MODEL" --host 127.0.0.1 --port 8082 \
    --prompt-cache-size 8 --decode-concurrency 2 --prompt-concurrency 2 > "$LOGS/llm.log" 2>&1 &
  pids+=($!)
  echo "Starting Gemma ($MODEL)…"
  wait_for 8082 "Gemma"
fi

if [[ -z "$NO_AVATAR" ]] && ! lsof -iTCP:8768 -sTCP:LISTEN >/dev/null 2>&1; then
  (cd "$HUGGINGBAY/interview-avatar" && PATH="$PWD/bin:$PATH" .venv/bin/python avatar/server.py) > "$LOGS/avatar.log" 2>&1 &
  pids+=($!)
  echo "Starting the avatar engine…"
  wait_for 8768 "Avatar engine"
fi

python3 "$HERE/model_gateway.py" --port 8090 > "$LOGS/gateway.log" 2>&1 &
pids+=($!)
wait_for 8090 "Gateway"

ngrok http 8090 --log "$LOGS/ngrok.log" > /dev/null 2>&1 &
pids+=($!)
URL=""
for i in {1..30}; do
  URL="$(curl -s http://127.0.0.1:4040/api/tunnels | python3 -c 'import json,sys; t=json.load(sys.stdin)["tunnels"]; print(next(x["public_url"] for x in t if x["public_url"].startswith("https")))' 2>/dev/null)" && [[ -n "$URL" ]] && break
  sleep 1
done
[[ -z "$URL" ]] && { echo "ngrok did not start (see $LOGS/ngrok.log)"; exit 1; }

cat <<EOF

Model host is up: $URL
Set these on the server (learning-service and interview-service), then restart them:

  LLM_PROVIDER=local
  LOCAL_LLM_URL=$URL/llm
  MODEL_HOST_KEY=$MODEL_HOST_KEY
  AVATAR_PROVIDER=${NO_AVATAR:+none}${NO_AVATAR:-local}
  LOCAL_AVATAR_URL=$URL/avatar

Check: curl -H "Authorization: Bearer \$(cat $KEY_FILE)" $URL/health
Logs: $LOGS. Keep this terminal open; Ctrl-C stops the model host.
EOF
wait
