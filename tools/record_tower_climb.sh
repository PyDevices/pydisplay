#!/bin/bash
set -euo pipefail
cd /workspace/src
OUT=/opt/cursor/artifacts/tower-climb-vertical-platformer.mp4
TRACE=/opt/cursor/artifacts/tower-climb-trace.jsonl
mkdir -p /opt/cursor/artifacts
rm -f "$TRACE"

find_win() {
  DISPLAY=:1 xwininfo -root -tree 2>/dev/null | rg "tower_climb\.py" | head -1 \
    | sed -E 's/^[[:space:]]*(0x[0-9a-f]+).*/\1/'
}

SESSION="tower-vid"
tmux -f /exec-daemon/tmux.portal.conf kill-session -t "$SESSION" 2>/dev/null || true
tmux -f /exec-daemon/tmux.portal.conf new-session -d -s "$SESSION" -c "/workspace/src" -- "${SHELL:-zsh}" -l
tmux -f /exec-daemon/tmux.portal.conf send-keys -t "$SESSION:0.0" \
  "TOWER_CLIMB_TRACE=$TRACE DISPLAY=:1 PYTHONPATH=lib ../.venv/bin/python examples/tower_climb.py" C-m

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

LINE=$(DISPLAY=:1 xwininfo -root -tree 2>/dev/null | rg "tower_climb\.py" | head -1)
# e.g. ... 640x960+1+28  +641+148
read -r W H X Y <<<"$(echo "$LINE" | sed -E 's/.* ([0-9]+)x([0-9]+)\+[0-9]+\+[0-9]+  \+([0-9]+)\+([0-9]+).*/\1 \2 \3 \4/')"
echo "WIN=$WIN ${W}x${H} at ${X},${Y}"

ffmpeg -y -f x11grab -draw_mouse 0 -framerate 24 \
  -video_size "${W}x${H}" -i ":1+${X},${Y}" \
  -t 12 -c:v libx264 -pix_fmt yuv420p "$OUT" &
FFPID=$!
sleep 2.0

WIN_DEC=$((WIN))
# Focus pygame window so keys reach the game
DISPLAY=:1 xdotool windowactivate --sync "$WIN_DEC" 2>/dev/null || true
sleep 0.3
# Dismiss splash screen
DISPLAY=:1 xdotool key --window "$WIN_DEC" Return 2>/dev/null || true
sleep 0.8

# Climb: run right, jump onto branches, repeat
for _ in $(seq 1 18); do
  DISPLAY=:1 xdotool key --window "$WIN_DEC" --delay 40 Right 2>/dev/null || true
  sleep 0.08
  DISPLAY=:1 xdotool key --window "$WIN_DEC" --delay 40 space 2>/dev/null || true
  sleep 0.45
  DISPLAY=:1 xdotool key --window "$WIN_DEC" --delay 40 Left 2>/dev/null || true
  sleep 0.08
  DISPLAY=:1 xdotool key --window "$WIN_DEC" --delay 40 space 2>/dev/null || true
  sleep 0.45
done

wait "$FFPID"
ls -lh "$OUT"
if [ -f "$TRACE" ]; then
  echo "TRACE=$TRACE ($(wc -l < "$TRACE") lines)"
fi
tmux -f /exec-daemon/tmux.portal.conf kill-session -t "$SESSION" 2>/dev/null || true
