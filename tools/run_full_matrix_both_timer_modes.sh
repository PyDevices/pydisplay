#!/usr/bin/env bash
# Run default example matrix for timer_async=False and True in parallel.
# Desktop subprocess runtimes only; example-major order.
set -euo pipefail
cd "$(dirname "$0")/.."

DESKTOP_RUNTIMES=(
  micropython
  micropython.exe
  circuitpython
  cpython-venv
  python.exe
)

export SDL_VIDEODRIVER=dummy
export SDL_AUDIODRIVER=dummy

run_mode() {
  local mode="$1"
  export PYDISPLAY_TIMER_ASYNC="${mode}"
  .venv/bin/python tools/example_test_kit.py \
    --no-unit-tests \
    --order examples \
    --only-runtime "${DESKTOP_RUNTIMES[@]}" \
    --results-json ".cursor/example_test_results_timer_async_${mode}.json" \
    2>&1 | tee ".cursor/matrix_timer_async_${mode}.log"
}

echo "Starting parallel desktop matrix: timer_async=0 and timer_async=1" >&2
run_mode 0 &
pid0=$!
run_mode 1 &
pid1=$!

status=0
wait "${pid0}" || status=$?
wait "${pid1}" || status=$?

if [[ "${status}" -eq 0 ]]; then
  echo "Done. Results:" >&2
  echo "  .cursor/example_test_results_timer_async_0.json" >&2
  echo "  .cursor/example_test_results_timer_async_1.json" >&2
fi
exit "${status}"
