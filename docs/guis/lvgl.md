# LVGL

Use the PyDevices display, input, and timing packages with [LVGL](https://lvgl.io/) — build full LVGL applications in pure Python and explore them through pydevices-examples.

The PyDevices LVGL **sister projects** bundle this integration for each runtime: [lvgl-micropython](https://github.com/PyDevices/lvgl-micropython) (MicroPython), [lvgl-circuitpython](https://github.com/PyDevices/lvgl-circuitpython) (CircuitPython), and [lvgl-python](https://github.com/PyDevices/lvgl-python) (CPython). Because they share `displaydev`, neutral board capabilities, and `multimer`, the same LVGL Python code is portable across all three — and you can even **develop it interactively in [Jupyter Notebook](../platforms/jupyter.md)**. See [Ecosystem & sister projects](../ecosystem.md).

The walkthrough below covers wiring pydevices-examples to LVGL manually (e.g. with upstream [lv_micropython](https://github.com/lvgl/lv_micropython)).

## Walkthrough

### 1. Install minimum PyDevices packages

--8<-- "_snippets/minimum-mip.md"

Or follow [pydevices install workflows](https://pydevices.github.io/pydevices/install-workflows.html) for current board setup.

### 2. Build or obtain LVGL MicroPython firmware

Follow upstream [lv_micropython](https://github.com/lvgl/lv_micropython) for your board. pydevices-examples supplies the flush and input glue via `board_config.py`; LVGL supplies the UI toolkit.

### 3. Wire board_config to LVGL

Your `board_config.py` should expose:

- `display_drv` — `displaydev` driver with `blit_rect`, dimensions, and rotation
- neutral input callables when present: `host_read`, `touch_read`,
  `keypad_read`, `encoder_read`, and `encoder_button_read`

Board configs describe hardware; they do not create an application runtime.
Connect LVGL's display flush callback to copy LVGL's draw buffer through
`display.blit_rect` (or use the packaged `display_driver`).

With [`display_driver`](https://github.com/PyDevices/lvgl-bindings/blob/main/python/display_driver.py), LVGL input is wired automatically through its own `LVGLRuntime` and virtual touch/encoder/keypad devices. **Do not instantiate or poll `eventsys` in an LVGL app** — `lv.task_handler()` (driven by `display_driver.event_loop` + `multimer`) already drains input. Window-close (`QUIT`) is handled by the bridge's `HostInput` path.

### 4. Run the LVGL timer example

Install examples package, then on device:

```python
import utils.path  # see ../utils.md#path-setup
import lv_test_timer
```

Requires LVGL-enabled firmware. See `src/examples/lv_test_timer.py` in the repo.

### 5. Faster ESP32 buses

For production ESP32 projects, consider [kdschlosser's lvgl_micropython](https://github.com/kdschlosser/lvgl_micropython) C drivers wired through `BusDisplay`.

## Helper add-ons

`display_driver` lives in [lvgl-bindings](https://github.com/PyDevices/lvgl-bindings) (`python/display_driver.py`) and ships with the LVGL sister projects (frozen in MP/CP firmwares; bundled with `pydevices-lvgl`). It requires a PyDevices `board_config`, `events`, `keys`, and `multimer`; it is independent of optional `eventsys`.

[`display_driver`](https://github.com/PyDevices/lvgl-bindings/blob/main/python/display_driver.py) includes the LVGL `event_loop` (requires `multimer`).

Use **`runtime.timer_async`** (derived from `board_config.timer_async` or the display driver's `requires_async_timer`) to inspect the selected timer backend:

| `runtime.timer_async` | Use when |
|---------------|----------|
| `False` (desktop default) | MCU, MicroPython unix, CPython Linux — default `multimer.Timer` |
| `True` | PyScript, Jupyter, or desktop with `PYDEVICES_TIMER_ASYNC=1` — `multimer.AsyncTimer` |

[`display_driver`](https://github.com/PyDevices/lvgl-bindings/blob/main/python/display_driver.py) passes this to `event_loop(asynchronous=runtime.timer_async)`.

When **`runtime.timer_async` is true**, `display_driver` drives ticks and `display.show()` from its asynchronous LVGL refresh loop.

Full apps typically build the UI then call **`runtime.run_forever()`** (see
[`lv_test_timer.py`](https://github.com/PyDevices/pydevices-examples/blob/main/src/examples/lv_test_timer.py)).

Desktop `board_config` reads **`PYDEVICES_TIMER_ASYNC`** for the PG/SDL
branch (default from `AutoDisplay`, normally `False`). PyScript and Jupyter
always use `timer_async=True`. Force async on desktop before `board_config` loads:

```python
import os
os.environ["PYDEVICES_TIMER_ASYNC"] = "1"
import display_driver
```

Or set `PYDEVICES_TIMER_ASYNC=1` on the command line when launching the process.

## Timer test example

[`lv_test_timer.py`](https://github.com/PyDevices/pydevices-examples/blob/main/src/examples/lv_test_timer.py) is a single smoke test that follows **`runtime.timer_async`** via `runtime.run_forever()` (interactive and kit). It does **not** read or write environment variables — set `PYDEVICES_TIMER_ASYNC` in the parent process / shell if you want a specific desktop mode before `board_config` loads.

The UI shows autodetected **runtime**, **OS**, **display** driver class, **timer** backend, **mode** (`sync`/`async`), and **LVGL** version, plus a seconds counter, spinning arc, and tap button.

### Automated kit mode

```bash
cd src
PYDEVICES_TIMER_ASYNC=0 .venv/bin/python examples/lv_test_timer.py kit
PYDEVICES_TIMER_ASYNC=1 .venv/bin/python examples/lv_test_timer.py kit
```

Kit mode runs a timed LVGL timer + input check, prints a `KIT_RESULT=` JSON line on stdout, then quits. Prefer [`tools/lv_timer_test_kit.py`](https://github.com/PyDevices/pydevices-examples/blob/main/tools/lv_timer_test_kit.py) to drive sync/async across desktop runtimes.

### Desktop test suite

[`tools/run_desktop_lv_tests.py`](https://github.com/PyDevices/pydevices-examples/blob/main/tools/run_desktop_lv_tests.py) runs the kit across **five desktop Python+LVGL executables** in sequence (ten subprocess runs total — `sync` and `async` per runtime).

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

The script prints a summary table (`queued` / `async` columns) and writes full results to a JSON file. Exit code **1** if any run hangs, crashes, fails timers, or fails click checks (strict policy).

For the full desktop matrix (micropython, circuitpython, cpython-venv, micropython.exe, python.exe × sync/async), use [`tools/lv_timer_test_kit.py`](https://github.com/PyDevices/pydevices-examples/blob/main/tools/lv_timer_test_kit.py):

```bash
python tools/lv_timer_test_kit.py
python tools/lv_timer_test_kit.py --only python.exe --modes sync
python tools/lv_timer_test_kit.py --only cpython-venv --modes sync async
```

The table shows the timer backend in each cell (e.g. `librt.Timer, ok` / `_async_timer, ok`).

[`tools/run_desktop_lv_tests.py`](https://github.com/PyDevices/pydevices-examples/blob/main/tools/run_desktop_lv_tests.py) is a shorter wrapper: same runtimes, **sync** and **async**, with strict click checks.

## Next

- [Architecture](../concepts/architecture.md)
- [Events](../concepts/events.md)
- [API reference → displaydev](../reference/overviews/displaydev.md)
