# LVGL

Use pydisplay as the display, input, and timing layer for [LVGL](https://lvgl.io/) — build full LVGL applications in pure Python.

The PyDevices LVGL **sister projects** bundle this integration for each runtime: [lv_micropython_cmod](https://github.com/PyDevices/lv_micropython_cmod) (MicroPython), [lv_circuitpython_mod](https://github.com/PyDevices/lv_circuitpython_mod) (CircuitPython), and [lv_cpython_mod](https://github.com/PyDevices/lv_cpython_mod) (CPython). Because they share pydisplay as the backend, the same LVGL Python code is portable across all three — and you can even **develop it interactively in [Jupyter Notebook](../platforms/jupyter.md)**. See [Ecosystem & sister projects](../ecosystem.md).

The walkthrough below covers wiring pydisplay to LVGL manually (e.g. with upstream [lv_micropython](https://github.com/lvgl/lv_micropython)).

## Walkthrough

### 1. Install minimum pydisplay packages

--8<-- "_snippets/minimum-mip.md"

Or use [installer.py](../installation/installer.md) for a one-shot setup.

### 2. Build or obtain LVGL MicroPython firmware

Follow upstream [lv_micropython](https://github.com/lvgl/lv_micropython) for your board. pydisplay supplies the flush and input glue via `board_config.py`; LVGL supplies the UI toolkit.

### 3. Wire board_config to LVGL

Your `board_config.py` should expose:

- `display_drv` — pydisplay driver with `blit_rect`, dimensions, rotation
- `runtime` — [eventsys Runtime](../concepts/runtime.md) with host/touch input and auto-refresh

Connect LVGL's display flush callback to copy LVGL's draw buffer through `display.blit_rect` (or the pattern documented in lv_micropython for your port).

With [`display_driver`](https://github.com/PyDevices/pydisplay/blob/main/src/add_ons/display_driver.py), LVGL input is wired automatically: each indev `read_cb` polls the runtime's host device via virtual touch/encoder/keypad devices. **Do not call `runtime.poll()` in your LVGL main loop** — `lv.task_handler()` (driven by `lv_utils` + multimer) already drains input. Calling both competes for the same event queue and breaks clicks. Window-close (`QUIT`) is handled on the same path inside `HostEventsDevice`.

### 4. Run the touch test example

Install examples package, then on device:

```python
import lib.path  # development layout only
import lv_touch_test
```

Requires LVGL-enabled firmware. See `src/examples/lv_touch_test.py` in the repo.

### 5. Faster ESP32 buses

For production ESP32 projects, consider [kdschlosser's lvgl_micropython](https://github.com/kdschlosser/lvgl_micropython) C drivers wired through `BusDisplay`.

## Helper add-ons

`src/add_ons/lv_utils.py` — LVGL event loop helper (requires `multimer`).

Use **`runtime.timer_async`** (set in `board_config.py` when constructing `Runtime`) to choose the timer backend:

| `runtime.timer_async` | Use when |
|---------------|----------|
| `False` (default) | MCU, MicroPython unix, CPython Linux — default `multimer.Timer` |
| `True` | PyScript and other asyncio-native apps — `multimer.AsyncTimer` |

[`display_driver`](https://github.com/PyDevices/pydisplay/blob/main/src/add_ons/display_driver.py) passes this to `lv_utils.event_loop(async_=runtime.timer_async)`.

When **`runtime.timer_async` is true**, `display_driver` claims runtime-driven refresh and calls `display.show()` from the aio LVGL refresh loop instead. CircuitPython's default `multimer.Timer` uses a background thread and requires `pump()` — which an asyncio app does not call — so the window would never be presented otherwise.

On CPython Win/mac (sync timers), call **`multimer.pump()`** from your main loop when using threaded timer backends — see [multimer](../concepts/multimer.md). Full apps call **`display_driver.run()`** after UI setup: it returns immediately on MicroPython unix and CPython Linux (REPL stays live) and blocks only on Windows SDL or macOS.

Force async mode before import (LVGL timer tests):

```python
import os
os.environ["PYDISPLAY_TIMER_ASYNC"] = "1"
import display_driver
```

## Timer test examples

Three scripts share the same UI via `lv_test_timer_common.build_ui()` and differ only in how multimer drives LVGL ticks:

| Script | When to run |
|--------|-------------|
| [`lv_test_timer_no_pump.py`](https://github.com/PyDevices/pydisplay/blob/main/src/examples/lv_test_timer_no_pump.py) | MCU, MP-unix, CPython Linux — no main loop; **hangs** on pump-required platforms |
| [`lv_test_timer_pump.py`](https://github.com/PyDevices/pydisplay/blob/main/src/examples/lv_test_timer_pump.py) | CPython Win/mac — `pump()` drain loop only |
| [`lv_test_timer_async.py`](https://github.com/PyDevices/pydisplay/blob/main/src/examples/lv_test_timer_async.py) | PyScript / asyncio — `PYDISPLAY_TIMER_ASYNC=1`, deferred `import display_driver`, `await asyncio.sleep(0)` loop |

The shared UI ([`lv_test_timer_common.py`](https://github.com/PyDevices/pydisplay/blob/main/src/examples/lv_test_timer_common.py)) shows autodetected **runtime**, **OS**, **display** driver class, **timer** backend, and **LVGL** version.

### Automated harness

[`lv_test_timer_harness.py`](https://github.com/PyDevices/pydisplay/blob/main/src/examples/lv_test_timer_harness.py) runs a timed LVGL timer + input check, prints a `KIT_RESULT=` JSON line on stdout, then injects `events.Quit` through the queue read path (same as clicking the window X) and expects the process to exit cleanly. Run from `src/`:

```bash
cd src
micropython examples/lv_test_timer_harness.py pump
.venv/bin/python examples/lv_test_timer_harness.py async
```

Modes: `no_pump`, `pump`, `async`.

### Desktop test suite

[`tools/run_desktop_lv_tests.py`](https://github.com/PyDevices/pydisplay/blob/main/tools/run_desktop_lv_tests.py) runs the harness across **five desktop Python+LVGL executables** in sequence (ten subprocess runs total — `pump` and `async` per runtime; **async is omitted on MicroPython Windows** because that port has no asyncio).

| Executable | How resolved |
|------------|--------------|
| MicroPython (Unix) | `micropython` on `PATH` |
| CircuitPython | `circuitpython` on `PATH` |
| MicroPython (Windows) | `micropython.exe` on `PATH` |
| CPython (Windows) | `python.exe` on `PATH` |
| CPython (Linux venv) | `.venv/bin/python` |

Each run uses `cwd=src/`, opens a window for ~4 s of timer/click checks, then injected quit; the child should print `KIT_RESULT=` and exit 0. Missing executables are skipped (`missing` in the summary table).

From the repository root:

```bash
python tools/run_desktop_lv_tests.py
./tools/run_desktop_lv_tests.py
```

From `src/`:

```bash
../tools/run_desktop_lv_tests.py
```

The script prints a summary table (`queued` / `async` columns) and writes full results to `.cursor/desktop_lv_test_results.json`. Exit code **1** if any run hangs, crashes, fails timers, or fails click checks (strict policy).

For the full desktop matrix (micropython, circuitpython, cpython-venv, micropython.exe, python.exe × sync/queued/async), use [`tools/lv_timer_test_kit.py`](https://github.com/PyDevices/pydisplay/blob/main/tools/lv_timer_test_kit.py):

```bash
python tools/lv_timer_test_kit.py
python tools/lv_timer_test_kit.py --only python.exe sync
python tools/lv_timer_test_kit.py --only cpython-venv --modes queued async
```

On Windows, **sync** uses the default **`multimer._win32`** backend (`needs_pump()` is false); the table shows the timer backend in each cell (e.g. `_win32, ok`).

[`tools/run_desktop_lv_tests.py`](https://github.com/PyDevices/pydisplay/blob/main/tools/run_desktop_lv_tests.py) is a shorter wrapper: same runtimes, **queued** and **async** only, with strict click checks.

## Next

- [Architecture](../concepts/architecture.md)
- [Events](../concepts/events.md)
- [API reference → displaysys](../reference/overviews/displaysys.md)
