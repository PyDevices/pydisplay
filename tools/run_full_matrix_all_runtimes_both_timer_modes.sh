#!/usr/bin/env bash
# Full-coverage matrix: one kit process per (runtime × timer_async) = 14 concurrent jobs.
# Each job focuses on a single runtime (--only-runtime). Modes 0 and 1 run in parallel.
# Report-only run after clearing matrix/skip_runtimes exclusions.
set -euo pipefail
cd "$(dirname "$0")/.."

RUNTIMES=(
  micropython
  micropython.exe
  circuitpython
  cpython-venv
  python.exe
  pyscript
  jupyter
)

export SDL_VIDEODRIVER=dummy
export SDL_AUDIODRIVER=dummy

run_one() {
  local mode="$1"
  local rt="$2"
  local safe
  safe="${rt//./_}"
  export PYDISPLAY_TIMER_ASYNC="${mode}"
  local json=".cursor/example_test_results_rt_${safe}_async_${mode}.json"
  local log=".cursor/matrix_rt_${safe}_async_${mode}.log"
  set +e
  .venv/bin/python tools/example_test_kit.py \
    --no-unit-tests \
    --all-except-harness \
    --order examples \
    --only-runtime "${rt}" \
    --results-json "${json}" \
    >"${log}" 2>&1
  local rc=$?
  set -e
  return "${rc}"
}

echo "Starting 14 concurrent jobs (7 runtimes × timer_async 0/1), one runtime per job" >&2

pids=()
declare -A pid_meta=()
for mode in 0 1; do
  for rt in "${RUNTIMES[@]}"; do
    run_one "${mode}" "${rt}" &
    pid=$!
    pids+=("${pid}")
    pid_meta["${pid}"]="${rt}/async=${mode}"
    echo "  spawned pid=${pid} ${rt} timer_async=${mode}" >&2
  done
done

status=0
for pid in "${pids[@]}"; do
  if ! wait "${pid}"; then
    status=$?
    echo "FAIL ${pid_meta[$pid]} (pid=${pid} exit=${status})" >&2
  else
    echo "OK   ${pid_meta[$pid]} (pid=${pid})" >&2
  fi
done

# Merge per-runtime shards into the two mode-level JSON files the report expects.
.venv/bin/python - <<'PY'
import json
from pathlib import Path
cursor = Path(".cursor")
for mode in ("0", "1"):
    rows = []
    for p in sorted(cursor.glob(f"example_test_results_rt_*_async_{mode}.json")):
        data = json.loads(p.read_text())
        chunk = data if isinstance(data, list) else data.get("results", [])
        rows.extend(r for r in chunk if r)
    out = cursor / f"example_test_results_timer_async_{mode}.json"
    out.write_text(json.dumps(rows, indent=2) + "\n")
    print(f"merged {len(rows)} rows -> {out}", flush=True)
PY

echo "Done (aggregate exit=${status}). Shards: .cursor/example_test_results_rt_*_async_{0,1}.json" >&2
echo "Merged: .cursor/example_test_results_timer_async_{0,1}.json" >&2
exit "${status}"
