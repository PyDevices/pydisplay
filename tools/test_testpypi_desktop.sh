#!/usr/bin/env bash
# Smoke-test PyDevices desktop wheels from TestPyPI in a throwaway venv.
#
# Installs displaysys-sdldisplay (SDL2 desktop backend + board_config), graphics-cmod,
# and lvgl-cpython, then runs a short import/draw check (opens a real SDL window by default).
#
# Usage (from repo root):
#   ./tools/test_testpypi_desktop.sh
#   ./tools/test_testpypi_desktop.sh --headless
#   TESTPYPI_VENV=/tmp/my-venv ./tools/test_testpypi_desktop.sh
#   ./tools/test_testpypi_desktop.sh --keep         # reuse venv path without deleting first
#   ./tools/test_testpypi_desktop.sh --headless --keep   # CI / no DISPLAY
#
# Requires: python3, pip. Uses two-index install (TestPyPI primary, PyPI for usdl2, etc.).
# See docs/publishing-micropython-lib.md#two-index-pip-install-required

set -euo pipefail

TESTPYPI_INDEX="${TESTPYPI_INDEX:-https://test.pypi.org/simple/}"
PYPI_INDEX="${PYPI_INDEX:-https://pypi.org/simple/}"
VENV="${TESTPYPI_VENV:-/tmp/pydisplay-testpypi-venv}"
KEEP=0
HEADLESS=0

usage() {
    cat <<'EOF'
Usage: ./tools/test_testpypi_desktop.sh [--headless] [--keep]

Create a venv, pip-install TestPyPI desktop packages (no version pins), and smoke-test:

  displaysys-sdldisplay  graphics-cmod  lvgl-cpython

Environment:
  TESTPYPI_VENV   venv directory (default: /tmp/pydisplay-testpypi-venv)
  TESTPYPI_INDEX  primary pip index (default: TestPyPI)
  PYPI_INDEX      extra-index-url (default: PyPI)

Options:
  --headless  Use SDL dummy video/audio (no window; for CI or SSH without DISPLAY)
  --keep      Do not delete the venv before install (still creates it if missing)
  -h          This help
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --keep)
            KEEP=1
            shift
            ;;
        --headless)
            HEADLESS=1
            shift
            ;;
        -h | --help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1" >&2
            usage >&2
            exit 1
            ;;
    esac
done

if [[ "$KEEP" -eq 0 ]]; then
    rm -rf "$VENV"
fi

python3 -m venv "$VENV"
"$VENV/bin/pip" install -q -U pip
"$VENV/bin/pip" install \
    -i "$TESTPYPI_INDEX" \
    --extra-index-url "$PYPI_INDEX" \
    displaysys-sdldisplay \
    graphics-cmod \
    lvgl-cpython

echo "--- installed ---"
"$VENV/bin/pip" freeze | sort
if [[ "$HEADLESS" -eq 1 ]]; then
    echo "--- smoke test (SDL dummy video) ---"
    export SDL_VIDEODRIVER=dummy
    export SDL_AUDIODRIVER=dummy
else
    echo "--- smoke test (SDL window) ---"
fi

set +e
"$VENV/bin/python" - <<'PY'
import graphics
import lvgl as lv

from board_config import display_drv, runtime

print("graphics:", graphics.implementation())
print("lvgl:", lv)
print("driver:", type(display_drv).__name__)
print("runtime:", type(runtime).__name__)

display_drv.fill(0xF800)
display_drv.show()
print("ok", display_drv.width, "x", display_drv.height)

if hasattr(display_drv, "quit"):
    display_drv.quit()
PY
ec=$?
set -e
if [[ $ec -ne 0 && $ec -ne 177 ]]; then
    exit "$ec"
fi

echo "Smoke test passed."
