#!/bin/zsh
# Shows whether the model host is up, locally and through the tunnel, and that the key is enforced.
KEY_FILE="$HOME/.skillbridge-local/model-host.key"
for p in 8082:Gemma 8090:gateway 8768:avatar 4040:ngrok; do
  lsof -iTCP:${p%%:*} -sTCP:LISTEN >/dev/null 2>&1 && echo "up    ${p#*:} (port ${p%%:*})" || echo "down  ${p#*:} (port ${p%%:*})"
done
URL="$(curl -s http://127.0.0.1:4040/api/tunnels 2>/dev/null | python3 -c 'import json,sys; print(next(t["public_url"] for t in json.load(sys.stdin)["tunnels"] if t["public_url"].startswith("https")))' 2>/dev/null)"
if [[ -z "$URL" ]]; then echo "Tunnel: not running"; exit 0; fi
echo "Tunnel: $URL"
echo "  without key -> HTTP $(curl -s -m 15 -o /dev/null -w '%{http_code}' "$URL/health") (must be 401)"
echo "  with key    -> $(curl -s -m 15 -H "Authorization: Bearer $(cat "$KEY_FILE")" "$URL/health")"
