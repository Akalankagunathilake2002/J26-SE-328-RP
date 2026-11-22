#!/bin/zsh
# Stops everything start-model-host.sh starts on this Mac: the tunnel first (nothing can reach the Mac
# any more), then the gateway, Gemma and the avatar engine. Safe to run when nothing is running.
stop() {  # pattern, name
  if pkill -f "$1" 2>/dev/null; then echo "Stopped $2"; else echo "$2 was not running"; fi
}
stop "ngrok http 8090" "ngrok tunnel"
stop "model_gateway.py" "gateway"
stop "mlx_lm.server" "Gemma"
stop "avatar/server.py" "avatar engine"
pkill -f "caffeinate -ims" 2>/dev/null
sleep 1
if lsof -iTCP -sTCP:LISTEN -P 2>/dev/null | grep -qE ":(8082|8090|8768|4040) "; then
  echo "Still listening:"; lsof -iTCP -sTCP:LISTEN -P | grep -E ":(8082|8090|8768|4040) "
else
  echo "All model host ports are closed (8082, 8090, 8768, 4040)."
fi
