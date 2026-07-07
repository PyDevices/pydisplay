#!/bin/bash
# Record one bot playthrough through the SUMMIT win screen (in-game frame capture).
set -euo pipefail
cd /workspace/src
OUT=/opt/cursor/artifacts/tower-climb-bot-win.mp4
TRACE=/opt/cursor/artifacts/tower-climb-bot-win-trace.jsonl
VIDEO_FPS="${TOWER_CLIMB_VIDEO_FPS:-12}"
MAX_WAIT="${TOWER_CLIMB_RECORD_MAX_WAIT:-180}"
mkdir -p /opt/cursor/artifacts
rm -f "$OUT" "$TRACE"

SESSION="tower-vid-win"
tmux -f /exec-daemon/tmux.portal.conf kill-session -t "$SESSION" 2>/dev/null || true
tmux -f /exec-daemon/tmux.portal.conf new-session -d -s "$SESSION" -c "/workspace/src" -- "${SHELL:-zsh}" -l
tmux -f /exec-daemon/tmux.portal.conf send-keys -t "$SESSION:0.0" \
  "TOWER_CLIMB_BOT=1 TOWER_CLIMB_HOLD_WIN=1 TOWER_CLIMB_VIDEO=$OUT TOWER_CLIMB_VIDEO_FPS=$VIDEO_FPS TOWER_CLIMB_TRACE=$TRACE DISPLAY=:1 PYTHONPATH=lib ../.venv/bin/python examples/tower_climb.py" C-m

DEADLINE=$((SECONDS + MAX_WAIT))
while [ "$SECONDS" -lt "$DEADLINE" ]; do
  if [ -f "$OUT" ] && [ -f "$TRACE" ] && rg -q '"kind":"win"' "$TRACE" 2>/dev/null; then
    if ! pgrep -f "examples/tower_climb.py" >/dev/null 2>&1; then
      break
    fi
  fi
  sleep 0.5
done

if pgrep -f "examples/tower_climb.py" >/dev/null 2>&1; then
  echo "timeout waiting for tower_climb.py to finish" >&2
  tmux -f /exec-daemon/tmux.portal.conf capture-pane -t "$SESSION:0.0" -p | tail -20 >&2
  pkill -f "examples/tower_climb.py" 2>/dev/null || true
  exit 1
fi

if [ ! -f "$OUT" ]; then
  echo "video not written: $OUT" >&2
  tmux -f /exec-daemon/tmux.portal.conf capture-pane -t "$SESSION:0.0" -p | tail -20 >&2
  exit 1
fi

ls -lh "$OUT"
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$OUT" \
  | awk '{printf "duration=%.1fs\n", $1}'

if [ -f "$TRACE" ]; then
  echo "TRACE=$TRACE ($(wc -l < "$TRACE") lines)"
  /workspace/.venv/bin/python - <<'PY' "$TRACE"
import json, sys
path = sys.argv[1]
ys = []
won = False
score = 0
for line in open(path, encoding="utf-8"):
    d = json.loads(line)
    if d["kind"] == "frame":
        ys.append(d["player"]["y"])
    if d["kind"] == "win":
        won = True
        score = d.get("score", 0)
if ys:
    print(f"trace ymin={min(ys):.1f} ymax={max(ys):.1f} frames={len(ys)} won={won} score={score}")
else:
    print("trace has no frame records")
    sys.exit(1)
if not won:
    print("FAIL: bot did not win during recording", file=sys.stderr)
    sys.exit(1)
print("OK: bot won")
PY
fi

tmux -f /exec-daemon/tmux.portal.conf kill-session -t "$SESSION" 2>/dev/null || true
