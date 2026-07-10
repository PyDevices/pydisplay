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

DEBUG_LOG=".cursor/debug-a4ac3e.log"
mkdir -p .cursor

# region agent log
_debug_log() {
  local hyp="$1" msg="$2" data="$3"
  .venv/bin/python -c "
import json, time
open('${DEBUG_LOG}','a').write(json.dumps({
  'sessionId':'a4ac3e','hypothesisId':'''${hyp}''','location':'run_full_matrix.sh',
  'message':'''${msg}''','data':json.loads('''${data}'''),'timestamp':int(time.time()*1000),
  'runId':'parallel-14'
})+'\n')
"
}
# endregion

run_one() {
  local mode="$1"
  local rt="$2"
  local safe
  safe="${rt//./_}"
  export PYDISPLAY_TIMER_ASYNC="${mode}"
  local json=".cursor/example_test_results_rt_${safe}_async_${mode}.json"
  local log=".cursor/matrix_rt_${safe}_async_${mode}.log"
  local t0
  t0=$(date +%s)
  # region agent log
  _debug_log "B" "worker_start" "{\"mode\":\"${mode}\",\"runtime\":\"${rt}\",\"pid\":$$,\"json\":\"${json}\"}"
  # endregion
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
  local t1 elapsed
  t1=$(date +%s)
  elapsed=$((t1 - t0))
  # region agent log
  _debug_log "A" "worker_done" "{\"mode\":\"${mode}\",\"runtime\":\"${rt}\",\"rc\":${rc},\"elapsed_s\":${elapsed},\"json\":\"${json}\"}"
  # endregion
  return "${rc}"
}

# region agent log
_debug_log "A" "matrix_launch" "{\"workers\":14,\"runtimes\":7,\"modes\":2,\"layout\":\"runtime_x_mode\"}"
# endregion

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

# region agent log
_debug_log "C" "all_spawned" "{\"pid_count\":${#pids[@]}}"
# endregion

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

# region agent log
_debug_log "D" "matrix_complete" "{\"aggregate_exit\":${status}}"
# endregion

echo "Done (aggregate exit=${status}). Shards: .cursor/example_test_results_rt_*_async_{0,1}.json" >&2
echo "Merged: .cursor/example_test_results_timer_async_{0,1}.json" >&2
exit "${status}"
