#!/usr/bin/env bash
# Clone palettes / pdwidgets / graphics siblings for local dev and example tests.
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
GRAPHICS="$(clone_or_update graphics)"

SITE="$("$ROOT/.venv/bin/python" -c 'import site; print(site.getsitepackages()[0])')"
echo "$PALETTES/lib" >"$SITE/palettes.pth"
echo "$PDWIDGETS/lib" >"$SITE/pdwidgets.pth"
echo "$GRAPHICS/lib" >"$SITE/graphics.pth"

export PYDISPLAY_PALETTES_LIB="$PALETTES/lib"
export PYDISPLAY_PDWIDGETS_LIB="$PDWIDGETS/lib"
export PYDISPLAY_GRAPHICS_LIB="$GRAPHICS/lib"

echo "palettes:  $PALETTES/lib"
echo "pdwidgets: $PDWIDGETS/lib"
echo "graphics:  $GRAPHICS/lib"
echo "CPython .pth files written under $SITE"
