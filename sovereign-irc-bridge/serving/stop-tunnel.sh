#!/usr/bin/env bash
# Stops a cloudflared quick tunnel if one was started (bridge + llama-server keep running on 127.0.0.1).
# Note: no tunnel is currently in use; the serving host's outbound network blocks Cloudflare tunnel edges.
# Env: RUN_DIR (where tunnel.pid would live).
RUN_DIR="${RUN_DIR:-${XDG_STATE_HOME:-$HOME/.local/state}/sovereign-bridge}"
PIDF="$RUN_DIR/tunnel.pid"
if [ -f "$PIDF" ] && kill "$(cat "$PIDF")" 2>/dev/null; then echo "tunnel stopped (pid $(cat "$PIDF"))"; else pkill -f 'cloudflared tunnel' && echo "tunnel stopped" || echo "no tunnel running"; fi
rm -f "$PIDF"
