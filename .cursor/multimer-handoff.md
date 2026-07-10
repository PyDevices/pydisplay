# Multimer / pydisplay Handoff

Date: 2026-07-05

This handoff captures the current local state after moving the recovered cloud-agent multimer implementation back into pydisplay and clarifying the new API goals.

## Current Repo State

- Repo: `/home/brad/github/pydisplay`
- Branch: `main`
- Remote state at last check: `main...origin/main`
- Working tree: dirty, uncommitted local changes
- PR #43 was merged earlier, so the new multimer package is already on `pydisplay` `main`.
- The standalone `~/github/multimer` repo still exists and should not be deleted until the pydisplay version is verified.

Important: the current pydisplay working tree is the active source of truth for the latest API decisions. The standalone `~/github/multimer` tests/package may lag behind the final decisions here.

## Agreed Multimer API Contract

Public API:

```python
from multimer import (
    Timer,       # init / deinit / ONE_SHOT / PERIODIC only
    AsyncTimer,  # same surface, requires a running event loop
    schedule,    # micropython.schedule-compatible
    sleep_ms,    # Adafruit-style bare sleep helper
    ticks_ms,
    ticks_add,
    ticks_diff,
    ticks_less,
    asyncio,     # lazy: frozen on MP/CP, stdlib on CPython
)
```

Not public and should not be reintroduced:

- `pump`
- `drain` / `_drain`
- `needs_pump`
- `periodic`
- `run_forever`, `dual_main`, app-loop helpers
- `capabilities`
- module-level `PERIODIC` / `ONE_SHOT`
- default tests that target private backend modules

Backend/private probing is allowed only during development, not as the normal production test kit surface. `tools/test_timers.py` supports this with `MULTIMER_PROBE_BACKENDS=1`.

## Design Goals

- `multimer.Timer` should behave like MicroPython `machine.Timer`.
- Timer callbacks should run on the main thread.
- `sleep_ms` is public, but it is **not** a pump/drain service point. It should be a simple Adafruit-style sleep helper.
- Do not consider pydisplay `auto_refresh`, LVGL ticks, or display loops while defining the multimer API.
- pydisplay migration strategy is to update call sites to `Timer` / `AsyncTimer`, not preserve old helpers.
- Threading and polling backends are likely temporary fallbacks. If the real platform backends succeed, they may be abandoned.

## What Was Changed Locally

### `src/lib/multimer`

- `__init__.py`
  - Exports `sleep_ms` publicly alongside `ticks_*`.
  - Public exports now match the contract above.

- `_ticks.py`
  - Defines `sleep_ms(ms)` as a plain Adafruit-style sleep helper.
  - Keeps `_sleep_ms = sleep_ms` as an internal alias for backends.
  - No drain, pump, polling tick, or APC servicing logic.

- `_schedule.py`
  - Removed `_drain` entirely.
  - CPython/CircuitPython `schedule(cb, arg)` now runs immediately only from the main thread.
  - Non-main-thread scheduling raises `RuntimeError`.
  - MicroPython still imports `micropython.schedule`.

- `_core.py`
  - Removed `_drain` import/use.
  - `_wait_idle()` now waits with internal `_sleep_ms(1)` while `_busy`.

- `_async_timer.py`, `_backends/threading.py`, `_backends/win32.py`
  - Removed positional-only `/` from constructors because MicroPython currently rejects that syntax.

- `_backends/librt.py`, `_backends/win32.py`
  - Documentation/comment cleanup to avoid implying app-side pump behavior.

### Tests

- Added `tests/test_multimer.py`.
  - Copied/ported from `~/github/multimer/tests/test_multimer.py`.
  - Tests public symbols only.
  - Adds `sleep_ms` to `__all__` expectation.
  - Adds callback main-thread assertions for `Timer` and `AsyncTimer`.
  - No tests of `_period_ms`, `_deliver`, private backend modules, pump, drain, or periodic helpers.

- Updated `tests/test_standalone.py`.
  - Isolated multimer subprocess imports public `sleep_ms`.
  - Still copies only `src/lib/multimer` into a temp dir.
  - Confirms no pydisplay sibling modules are imported.

- Updated `tests/_support.py`.
  - Removed dead `_support.pump()` helper.

- Replaced `tests/test_auto_refresh.py` with a skipped placeholder.
  - Reason: auto-refresh migration to `Timer` / `AsyncTimer` is pending.
  - The old tests asserted removed APIs (`multimer.pump`, `multimer.periodic`).

- Updated `tests/test_jndisplay_scroll.py`.
  - No longer patches `multimer.periodic`.
  - Bypasses `DisplayDriver.__init__` for scroll-rendering tests.

- Updated `tests/README.md`.
  - Describes in-tree multimer tests and removes old `pump` / `periodic` test descriptions.

### Tools / Harness

- `tools/test_timers.py`
  - Default probe surface is public only:
    - `machine.Timer`
    - `AsyncTimer`
    - `AsyncTimer (yield loop)`
    - `multimer.Timer (default)`
  - Uses public `sleep_ms`.
  - Private backend probes are development-only behind `MULTIMER_PROBE_BACKENDS=1`.

- `tools/run_test_timers.py`
  - Report columns match public probes only.

- `tools/example_test_manifest.toml`
  - Added `bootstrap = "headless"` for `test_timers`.

- `tools/example_test_wrapper.py`
  - Supports headless bootstrap so timer probes do not initialize display/board config.
  - Uses plain `time.sleep` for wrapper sleeps.

- `tools/example_test_kit.py`
  - Passes `--bootstrap`.
  - Summarizes headless success as `ok`.

- `tools/quit_inject.py`
  - Renamed helper behavior away from multimer pumping (`service_host_events`).
  - Still contains broader LVGL/test harness language using “pump” as a mode name in other files; this is not multimer API usage.

- `src/lib/path.py`
  - Suppresses path chatter when `pydisplay_test_mode.ENABLED` is set by the wrapper.

## Verification Already Run

Focused multimer tests:

```bash
cd /home/brad/github/pydisplay
python3 -m unittest discover -s tests -p 'test_multimer.py' -v
python3 -m unittest discover -s tests -p 'test_standalone.py' -k multimer -v
python3 tools/test_timers.py
```

Result: passed.

Runtime matrix:

```bash
cd /home/brad/github/pydisplay
python3 tools/run_test_timers.py
```

Result: `ok` across:

- `micropython`
- `micropython.exe`
- `circuitpython`
- `cpython-venv`
- `python.exe`

Affected pydisplay tests:

```bash
python3 -m unittest discover -s tests -p 'test_jndisplay_scroll.py' -v
python3 -m unittest discover -s tests -p 'test_auto_refresh.py' -v
```

Result: OK with skips (`jndisplay` dependencies absent locally; `auto_refresh` intentionally skipped).

Lints:

```text
ReadLints: no linter errors found for edited paths.
```

## Useful Scans

These were clean for `tests/` and `src/lib/multimer` after the latest edits:

```bash
rg '_drain|\bdrain\b|multimer\.pump|\bpump\(|multimer\.periodic|\bperiodic\b|_period_ms|_deliver' \
  tests src/lib/multimer
```

Note: broader `tools/` still has LVGL mode names like `pump`; those are separate LVGL harness terminology and not public multimer API calls.

## Current Dirty Files

At last check:

```text
 M docs/testing/test_timers_report.md
 M src/lib/multimer/__init__.py
 M src/lib/multimer/_async_timer.py
 M src/lib/multimer/_backends/librt.py
 M src/lib/multimer/_backends/threading.py
 M src/lib/multimer/_backends/win32.py
 M src/lib/multimer/_core.py
 M src/lib/multimer/_schedule.py
 M src/lib/multimer/_ticks.py
 M src/lib/path.py
 M tests/README.md
 M tests/_support.py
 M tests/test_auto_refresh.py
 M tests/test_jndisplay_scroll.py
 M tests/test_standalone.py
 M tools/example_test_kit.py
 M tools/example_test_manifest.toml
 M tools/example_test_wrapper.py
 M tools/quit_inject.py
 M tools/run_test_timers.py
 M tools/test_timers.py
?? tests/test_multimer.py
?? MULTIMER_HANDOFF.md
```

No commit has been made for these latest changes.

## Suggested Next Steps In pydisplay Workspace

1. Reopen `/home/brad/github/pydisplay`.
2. Review the dirty tree carefully.
3. Run focused checks again:

   ```bash
   python3 -m unittest discover -s tests -p 'test_multimer.py' -v
   python3 -m unittest discover -s tests -p 'test_standalone.py' -k multimer -v
   python3 tools/run_test_timers.py
   ```

4. Decide whether to keep `tests/test_auto_refresh.py` as a skipped placeholder or delete it until the pydisplay migration.
5. Commit the multimer API/test-kit cleanup once reviewed.
6. Later: migrate pydisplay call sites (`auto_refresh`, LVGL helpers, examples, docs) to `Timer` / `AsyncTimer`.
7. Only after pydisplay main is verified end-to-end, delete the standalone `PyDevices/multimer` repo if still desired.

