#!/usr/bin/env bash
# Start pydisplay's PyScript dev server and open an example in the browser.
#
# Usage (from repo root):
#   ./tools/pyscript.sh chango
#   ./tools/pyscript.sh calculator
#   ./tools/pyscript.sh --manifest chango
#   ./tools/pyscript.sh --module calculator
#   ./tools/pyscript.sh                         # gallery (index.html)
#   ./tools/pyscript.sh chango -p 8080
#   ./tools/pyscript.sh chango --no-open

set -euo pipefail

_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYDISPLAY_ROOT="${PYDISPLAY_ROOT:-$(cd "$_SCRIPT_DIR/.." && pwd)}"
SERVE="$PYDISPLAY_ROOT/tools/serve.py"
PYSCRIPT_DIR="$PYDISPLAY_ROOT/web/pyscript"
PORT=8000
DEMO=""
MODE="" # manifest | module | hub
OPEN=1
DEBUG=0

usage() {
  cat <<EOF
Usage: ./tools/pyscript.sh [DEMO] [options]

  DEMO              manifest or module name (default: open gallery)
  --manifest NAME   load web/pyscript/NAME.json via embed.html?manifests=
  --module NAME     load src/examples/NAME.py via embed.html?modules=
  -p, --port PORT   port (default: 8000)
  --debug           append ?debug=1 (show log panel on embed.html)
  --no-open         start server and print URL; do not open a browser
  -h, --help        this help

Environment:
  PYDISPLAY_ROOT    pydisplay clone (default: parent of tools/)

Examples:
  ./tools/pyscript.sh chango
  ./tools/pyscript.sh --module calculator
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help)
      usage
      exit 0
      ;;
    --manifest)
      MODE=manifest
      DEMO="${2:?--manifest requires a name}"
      shift 2
      ;;
    --module)
      MODE=module
      DEMO="${2:?--module requires a name}"
      shift 2
      ;;
    -p|--port)
      PORT="${2:?--port requires a number}"
      shift 2
      ;;
    --debug)
      DEBUG=1
      shift
      ;;
    --no-open)
      OPEN=0
      shift
      ;;
    --*)
      echo "pyscript.sh: unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
    *)
      if [[ -n "$DEMO" ]]; then
        echo "pyscript.sh: unexpected argument: $1" >&2
        usage >&2
        exit 1
      fi
      DEMO="$1"
      shift
      ;;
  esac
done

if [[ ! -f "$SERVE" ]]; then
  echo "pyscript.sh: serve.py not found: $SERVE" >&2
  exit 1
fi

if [[ -z "$MODE" && -n "$DEMO" ]]; then
  if [[ -f "$PYSCRIPT_DIR/${DEMO}.json" ]]; then
    MODE=manifest
  elif [[ -f "$PYDISPLAY_ROOT/src/examples/${DEMO}.py" ]]; then
    MODE=module
  else
    echo "pyscript.sh: no manifest web/pyscript/${DEMO}.json or module src/examples/${DEMO}.py" >&2
    exit 1
  fi
fi

BASE="http://127.0.0.1:${PORT}"
if [[ -z "$DEMO" || "$MODE" == "hub" ]]; then
  URL="${BASE}/web/pyscript/index.html"
elif [[ "$MODE" == "manifest" ]]; then
  URL="${BASE}/web/pyscript/embed.html?manifests=${DEMO}"
elif [[ "$MODE" == "module" ]]; then
  URL="${BASE}/web/pyscript/embed.html?modules=${DEMO}"
fi

if [[ "$DEBUG" -eq 1 ]]; then
  if [[ "$URL" == *"?"* ]]; then
    URL="${URL}&debug=1"
  else
    URL="${URL}?debug=1"
  fi
fi

server_ready() {
  curl -sf -o /dev/null "${BASE}/web/pyscript/embed.html" 2>/dev/null
}

wait_for_server() {
  local i
  for i in $(seq 1 50); do
    if server_ready; then
      return 0
    fi
    sleep 0.1
  done
  return 1
}

open_url() {
  local url="$1"
  if [[ "$OPEN" -eq 0 ]]; then
    return 0
  fi
  if command -v xdg-open >/dev/null 2>&1; then
    xdg-open "$url" >/dev/null 2>&1 &
  elif command -v wslview >/dev/null 2>&1; then
    wslview "$url" >/dev/null 2>&1 &
  elif [[ -n "${WSL_DISTRO_NAME:-}" ]] && command -v cmd.exe >/dev/null 2>&1; then
    cmd.exe /c start "" "$url" >/dev/null 2>&1 &
  else
    echo "pyscript.sh: no browser opener found; open manually:"
    echo "  $url"
    return 0
  fi
}

SERVER_PID=""
cleanup() {
  if [[ -n "$SERVER_PID" ]]; then
    kill "$SERVER_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

if server_ready; then
  echo "pyscript.sh: reusing server at ${BASE}"
else
  echo "pyscript.sh: starting ${SERVE} on ${BASE}"
  python3 "$SERVE" -p "$PORT" &
  SERVER_PID=$!
  if ! wait_for_server; then
    echo "pyscript.sh: server did not become ready on ${BASE}" >&2
    exit 1
  fi
fi

echo "pyscript.sh: ${URL}"
open_url "$URL"

if [[ -n "$SERVER_PID" ]]; then
  echo "pyscript.sh: Ctrl+C to stop the server"
  wait "$SERVER_PID"
fi
