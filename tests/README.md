# Tests

Self-contained tests for the standalone [`multimer`](../src/lib/multimer) and
[`eventsys`](../src/lib/eventsys) packages.

They use only the Python standard library (`unittest`) — no third-party test
runner or build step is required. The shared bootstrap in
[`_env.py`](_env.py) puts `src/lib` on `sys.path`, so nothing needs to be
installed first.

## Running

From the repository root:

```bash
python -m unittest discover -s tests -v
```

Or run a single module:

```bash
python -m unittest tests.test_ticks -v
# or
python tests/test_ticks.py
```

## What is covered

| Module | Area |
|--------|------|
| `test_ticks.py` | `ticks_ms` / `ticks_add` / `ticks_diff` / `ticks_less` / `sleep_ms` |
| `test_schedule.py` | `schedule` / `run_queued` and the `REQUIRES_RUN_QUEUED` flag |
| `test_timer.py` | the default `multimer.Timer` (whichever backend is selected) |
| `test_get_timer.py` | the `get_timer` convenience helper |
| `test_aio.py` | the opt-in `multimer.aio` asyncio timer |
| `test_events.py` | the `events` types/classes and `eventsys.custom_type` |
| `test_devices.py` | `Broker` and the `Queue`/`Touch`/`Encoder`/`Keypad` devices plus `devices.custom_type` |
| `test_keys.py` | the `Keys` key/modifier tables and `keyname`/`key`/`modname`/`mod` helpers |
| `test_standalone.py` | proves each package imports and runs with **none** of the rest of pydisplay on the path |

The timer tests run on whichever synchronous backend the host selects
(`_ctypes`/`_ffi`/`_threading`/`_sdl2`/`_polling`); `_support.pump()` drives
them uniformly. Tests that need a real `machine.Timer` are skipped when no
backend is available.

The device tests drive each device through its `poll()` method using small
scripted `read` callbacks from [`_support.py`](_support.py), so they run
identically on every host without any hardware.
