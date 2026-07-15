#!/usr/bin/env bash
# Clone palettes / pdwidgets siblings for local dev and example tests.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEST="${PYDISPLAY_SIBLINGS_DIR:-/tmp/pydevices-siblings}"
mkdir -p "$DEST"

clone_or_update() {
  local name="$1"
  local url="https://github.com/PyDevices/${name}.git"
  local dir="$DEST/$name"
  if [[ -d "$dir/.git" ]]; then
    git -C "$dir" fetch --depth 1 origin main
    git -C "$dir" checkout -q main
    git -C "$dir" reset --hard -q origin/main
  else
    git clone --depth 1 "$url" "$dir"
  fi
  echo "$dir"
}

PALETTES="$(clone_or_update palettes)"
PDWIDGETS="$(clone_or_update pdwidgets)"

SITE="$("$ROOT/.venv/bin/python" -c 'import site; print(site.getsitepackages()[0])')"
echo "$PALETTES/src" >"$SITE/palettes.pth"
echo "$PDWIDGETS/src" >"$SITE/pdwidgets.pth"

export PYDISPLAY_PALETTES_SRC="$PALETTES/src"
export PYDISPLAY_PDWIDGETS_SRC="$PDWIDGETS/src"

echo "palettes:  $PALETTES/src"
echo "pdwidgets: $PDWIDGETS/src"
echo "CPython .pth files written under $SITE"
