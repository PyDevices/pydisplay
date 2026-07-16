#!/usr/bin/env bash
# Verify PyDevices TestPyPI wheels import alone (no sibling pydisplay libs pre-installed).
#
# Each package gets a fresh venv with only that wheel (+ pip-resolved deps from its
# manifest). Fails if import or a minimal smoke check errors.
#
# Usage:
#   ./tools/test_testpypi_standalone.sh
#   ./tools/test_testpypi_standalone.sh --desktop   # also sdldisplay + pgdisplay stacks
#
# See docs/publishing-micropython-lib.md#two-index-pip-install-required

set -euo pipefail

TESTPYPI_INDEX="${TESTPYPI_INDEX:-https://test.pypi.org/simple/}"
PYPI_INDEX="${PYPI_INDEX:-https://pypi.org/simple/}"
BASE_VENV="${TESTPYPI_STANDALONE_VENV:-/tmp/pydisplay-testpypi-standalone}"
DESKTOP=0

usage() {
    cat <<'EOF'
Usage: ./tools/test_testpypi_standalone.sh [--desktop]

Install each TestPyPI package into its own venv and run a minimal import smoke test.

Options:
  --desktop  Also test displaysys-sdldisplay and displaysys-pgdisplay (headless SDL/pg)
  -h         This help
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --desktop)
            DESKTOP=1
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

check_import() {
    local venv="$1"
    local py_code="$2"
    set +e
    SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy "$venv/bin/python" -c "$py_code"
    local ec=$?
    set -e
    # usdl2/SDL may deliver SIGRTMIN+15 during interpreter teardown after a successful run
    if [[ $ec -eq 0 || $ec -eq 177 ]]; then
        return 0
    fi
    exit "$ec"
}

test_package() {
    local pypi_name="$1"
    local py_code="$2"
    shift 2
    local extras=("$@")
    local venv="${BASE_VENV}-${pypi_name}"

    rm -rf "$venv"
    python3 -m venv "$venv"
    "$venv/bin/pip" install -q -U pip
    "$venv/bin/pip" install -i "$TESTPYPI_INDEX" --extra-index-url "$PYPI_INDEX" \
        "$pypi_name" "${extras[@]}"
    echo "--- $pypi_name ---"
    "$venv/bin/pip" freeze | sort
    check_import "$venv" "$py_code"
    echo "ok: $pypi_name"
    echo
}

test_package multimer "import multimer; print('multimer', multimer.Timer)"

test_package displaysys "import displaysys; print('displaysys', displaysys.DisplayDriver.__name__)"

test_package eventsys "
import eventsys
r = eventsys.Runtime()
r.start_timer()
print('eventsys', type(r).__name__)
"

test_package pydisplay-graphics "import graphics; print('graphics', graphics.implementation())"

if [[ "$DESKTOP" -eq 1 ]]; then
    # usdl2 / pygame-ce are runtime deps, not pip requires of the displaysys-* wheels.
    test_package displaysys-sdldisplay "
from board_config import display_drv
print('sdldisplay', type(display_drv).__name__)
display_drv.fill(0)
display_drv.show()
" usdl2

    test_package displaysys-pgdisplay "
from displaysys.pgdisplay import PGDisplay
print('pgdisplay', PGDisplay.__name__)
" pygame-ce
fi

echo "All standalone TestPyPI smoke tests passed."
