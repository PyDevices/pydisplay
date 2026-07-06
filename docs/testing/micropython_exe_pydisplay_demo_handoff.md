# MicroPython.exe pydisplay demo handoff

Date: 2026-07-06

## Scope

This handoff covers the current `micropython.exe` work on:

- `src/examples/pydisplay_demo.py`
- `src/examples/pydisplay_demo_async.py`
- `src/lib/multimer/_backends/sdl2.py`
- `src/lib/multimer/loop.py`
- `tools/example_test_wrapper.py`

The goal was to get both pydisplay demos running under `micropython.exe` while preserving the native SDL2 timer backend. Debugging has been paused with `exit_3` addressed for the sync path and the remaining failures documented below.

## Current code state

Temporary debug instrumentation has been removed. The remaining intentional code changes are:

- `src/lib/multimer/_backends/sdl2.py`: native SDL2 backend restored. `Timer._handler()` catches `RuntimeError` from `schedule(...)`, clears `_pending`, and returns `interval` instead of letting `RuntimeError: schedule queue full` terminate the process.
- `src/lib/multimer/loop.py`: `run_forever_async()` now drains `_run_pending()` and the selected backend drain hook before `await asyncio.sleep(...)`.
- `tools/example_test_wrapper.py`: fallback multimer quit/touch timers are kept in `_MULTIMER_TEST_TIMERS` so they are not collected before firing. The wrapper also initializes `quit_inject.queue_device()` before arming the fallback timer.

## Runtime evidence

Commands used:

```sh
.venv/bin/python tools/example_test_kit.py --only-example pydisplay_demo --only-runtime micropython.exe
.venv/bin/python tools/example_test_kit.py --only-example pydisplay_demo_async --only-runtime micropython.exe
```

Observed results after cleanup:

- `pydisplay_demo @ micropython.exe`: `exit_5`
- `pydisplay_demo_async @ micropython.exe`: after the async drain change, no longer reports `exit_3`; current result is `hang`

The latest `.cursor/example_test_results.json` only contains the most recent async run:

```json
[
  {
    "example": "pydisplay_demo_async",
    "runtime": "micropython.exe",
    "summary": "hang",
    "returncode": -1,
    "timed_out": true,
    "duration_s": 5.0,
    "timeout_s": 60.0,
    "result": null,
    "stdout_tail": "",
    "stderr_tail": ""
  }
]
```

## What fixed exit_3

There were two separate `exit_3` failure modes:

1. Sync demo: SDL timer callback raised `RuntimeError: schedule queue full` in `src/lib/multimer/_backends/sdl2.py`.
   - Fix kept: catch `RuntimeError`, clear `_pending`, and return `interval`.
   - Verification: sync moved from `exit_3` to `exit_5`.

2. Async demo: `run_forever_async()` used `asyncio.sleep()` without draining multimer pending callbacks / SDL scheduler.
   - Fix kept: call `_run_pending()` and `_backend_drain()` inside `run_forever_async()` before sleeping.
   - Verification: async moved from `exit_3` to `hang`.

## Rejected / reverted experiments

These were tried during debugging and should not be treated as current fixes:

- Increasing `usdl2.pump_scheduler(...)` budget from `32` to `256`.
- Delivering SDL timer callbacks directly instead of through `schedule()`.
- Replacing the SDL2 backend with a cooperative polling timer list.
- Heavy debug logging in `_ticks.py`, `loop.py`, `sdldisplay.py`, `pydisplay_demo.py`, and `example_test_wrapper.py`.

## Remaining work

Remaining known issues:

- Sync demo: `exit_5` remains.
- Async demo: current state is `hang` after fixing the `exit_3` queue-full failure.

Recommended next debugging pass:

1. Keep the current native SDL2 backend.
2. Reproduce the async hang with targeted instrumentation around:
   - `multimer.loop.run_forever_async()`
   - `tools/example_test_wrapper._start_multimer_quit_schedule()`
   - `quit_inject.inject_quit()`
   - `pydisplay_demo_async.handle_events()`
3. Verify whether the fallback quit timer fires and whether the injected quit event is observed by `broker.poll()`.
4. For sync `exit_5`, instrument only the post-quit / process-exit path after confirming the demo loop reaches or misses the quit event.

## Useful notes

- Always run desktop Python via `.venv/bin/python`; there is no `.venv` for `python.exe`.
- The debug session log path used in this investigation was `.cursor/debug-b26744.log`, but debug instrumentation has been removed.
- The primary signal for the original `exit_3` was repeated `SDL timer schedule queue full` in stderr.
