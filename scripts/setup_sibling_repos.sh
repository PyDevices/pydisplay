#!/usr/bin/env bash
# Clone palettes / pdwidgets / pygraphics / usdl2 siblings for local dev and example tests.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEST="${PYDEVICES_SIBLINGS_DIR:-/tmp/pydevices-siblings}"
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
GRAPHICS="$(clone_or_update pygraphics)"
USDL2="$(clone_or_update usdl2)"

SITE="$("$ROOT/.venv/bin/python" -c 'import site; print(site.getsitepackages()[0])')"
echo "$PALETTES/lib" >"$SITE/palettes.pth"
echo "$PDWIDGETS/lib" >"$SITE/pdwidgets.pth"
echo "$GRAPHICS/lib" >"$SITE/pygraphics.pth"
echo "$USDL2/lib" >"$SITE/usdl2.pth"

export PYDEVICES_PALETTES_LIB="$PALETTES/lib"
export PYDEVICES_PDWIDGETS_LIB="$PDWIDGETS/lib"
export PYDEVICES_PYGRAPHICS_LIB="$GRAPHICS/lib"
export PYDEVICES_USDL2_LIB="$USDL2/lib"

echo "palettes:  $PALETTES/lib"
echo "pdwidgets: $PDWIDGETS/lib"
echo "pygraphics:  $GRAPHICS/lib"
echo "usdl2:     $USDL2/lib"
echo "CPython .pth files written under $SITE"
