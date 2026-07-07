#!/bin/bash
set -euo pipefail
cd /workspace/src
OUT=/opt/cursor/artifacts/tower-climb-vertical-platformer.mp4
TRACE=/opt/cursor/artifacts/tower-climb-trace.jsonl
DURATION="${TOWER_CLIMB_RECORD_SECONDS:-18}"
mkdir -p /opt/cursor/artifacts
rm -f "$TRACE"

find_win() {
  DISPLAY=:1 xwininfo -root -tree 2>/dev/null | rg "tower_climb\.py" | head -1 \
    | sed -E 's/^[[:space:]]*(0x[0-9a-f]+).*/\1/'
}

win_geom() {
  DISPLAY=:1 xwininfo -id "$1" 2>/dev/null \
    | awk '/Absolute upper-left X:|Absolute upper-left Y:|Width:|Height:/ {print $NF}'
}

SESSION="tower-vid"
tmux -f /exec-daemon/tmux.portal.conf kill-session -t "$SESSION" 2>/dev/null || true
tmux -f /exec-daemon/tmux.portal.conf new-session -d -s "$SESSION" -c "/workspace/src" -- "${SHELL:-zsh}" -l
tmux -f /exec-daemon/tmux.portal.conf send-keys -t "$SESSION:0.0" \
  "TOWER_CLIMB_RECORD=1 TOWER_CLIMB_TRACE=$TRACE DISPLAY=:1 PYTHONPATH=lib ../.venv/bin/python examples/tower_climb.py" C-m

WIN=""
for _ in $(seq 1 50); do
  WIN=$(find_win || true)
  [ -n "$WIN" ] && break
  sleep 0.2
done

if [ -z "$WIN" ]; then
  echo "window not found" >&2
  tmux -f /exec-daemon/tmux.portal.conf capture-pane -t "$SESSION:0.0" -p | tail -10 >&2
  exit 1
fi

read -r X Y W H <<<"$(win_geom "$WIN" | tr '\n' ' ')"
echo "WIN=$WIN ${W}x${H} at ${X},${Y}"

# Let the game present a few frames before capture starts.
sleep 1.0

ffmpeg -y -f x11grab -draw_mouse 0 -framerate 24 \
  -video_size "${W}x${H}" -i ":1+${X},${Y}" \
  -t "$DURATION" -c:v libx264 -pix_fmt yuv420p "$OUT" &
FFPID=$!

wait "$FFPID"
ls -lh "$OUT"

if [ -f "$TRACE" ]; then
  echo "TRACE=$TRACE ($(wc -l < "$TRACE") lines)"
  /workspace/.venv/bin/python - <<'PY' "$TRACE"
import json, sys
path = sys.argv[1]
ys = []
won = False
for line in open(path, encoding="utf-8"):
    d = json.loads(line)
    if d["kind"] == "frame":
        ys.append(d["player"]["y"])
    if d["kind"] == "win":
        won = True
if ys:
    print(f"trace ymin={min(ys):.1f} ymax={max(ys):.1f} frames={len(ys)} won={won}")
else:
    print("trace has no frame records")
PY
fi

tmux -f /exec-daemon/tmux.portal.conf kill-session -t "$SESSION" 2>/dev/null || true
