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

With [`display_driver`](https://github.com/PyDevices/pydisplay/blob/main/src/add_ons/display_driver.py), LVGL input is wired automatically: each indev `read_cb` polls the runtime's host device via virtual touch/encoder/keypad devices. **Do not call `runtime.poll()` in your LVGL main loop** — `lv.task_handler()` (driven by `display_driver.event_loop` + multimer) already drains input. Calling both competes for the same event queue and breaks clicks. Window-close (`QUIT`) is handled on the same path inside `HostEventsDevice`.

### Display rotation

Set `display_drv.rotation` to `0`, `90`, `180`, or `270` **before** `import display_driver`.

- **Hardware rotation** (`BusDisplay` MADCTL, SDL/PG): `supports_hw_rotation` is true — LVGL uses the logical size; the driver remaps pixels.
- **Software rotation** (RGB / `FBDisplay` and other framebuffer scanout): LVGL `display_t.set_rotation` plus per-dirty-tile `draw_sw_rotate` in the flush callback. Touch points are mapped to logical coordinates. Cost scales with dirty area size.

Example (portrait UI on a landscape-native RGB panel):

```python
from board_config import display_drv, runtime

display_drv.rotation = 90
import display_driver  # noqa: E402
```

Or set `PYDISPLAY_LV_ROTATION=90` before launch when using `lv_test_timer` (see below).

### 4. Run the LVGL timer example

Install examples package, then on device:

```python
import lib.path  # development layout only
import lv_test_timer
```

Requires LVGL-enabled firmware. See `src/examples/lv_test_timer.py` in the repo.

### 5. Faster ESP32 buses

For production ESP32 projects, consider [kdschlosser's lvgl_micropython](https://github.com/kdschlosser/lvgl_micropython) C drivers wired through `BusDisplay`.

## Helper add-ons

[`display_driver`](https://github.com/PyDevices/pydisplay/blob/main/src/add_ons/display_driver.py) includes the LVGL `event_loop` (requires `multimer`).

Use **`runtime.timer_async`** (set in `board_config.py` when constructing `Runtime`) to choose the timer backend:

| `runtime.timer_async` | Use when |
|---------------|----------|
| `False` (desktop default) | MCU, MicroPython unix, CPython Linux — default `multimer.Timer` |
| `True` | PyScript, Jupyter, or desktop with `PYDISPLAY_TIMER_ASYNC=1` — `multimer.AsyncTimer` |

[`display_driver`](https://github.com/PyDevices/pydisplay/blob/main/src/add_ons/display_driver.py) passes this to `event_loop(asynchronous=runtime.timer_async)`.

When **`runtime.timer_async` is true**, `display_driver` claims runtime-driven refresh and calls `display.show()` from the aio LVGL refresh loop instead — so presentation stays on the asyncio path even when a sync timer backend would otherwise be used.

Full apps typically build the UI then call **`runtime.run_forever()`** (see
[`lv_test_timer.py`](https://github.com/PyDevices/pydisplay/blob/main/src/examples/lv_test_timer.py)).

`src/lib/board_config.py` reads **`PYDISPLAY_TIMER_ASYNC`** for the PG/SDL
desktop branch (default `False`). PyScript and Jupyter always use
`timer_async=True`. Force async on desktop before `board_config` loads:

```python
import os
os.environ["PYDISPLAY_TIMER_ASYNC"] = "1"
import display_driver
```

Or set `PYDISPLAY_TIMER_ASYNC=1` on the command line when launching the process.

## Timer test example

[`lv_test_timer.py`](https://github.com/PyDevices/pydisplay/blob/main/src/examples/lv_test_timer.py) is a single smoke test that follows **`runtime.timer_async`** via `runtime.run_forever()` (interactive and kit). Set parent-process env before launch:

| Variable | Effect |
|----------|--------|
| `PYDISPLAY_TIMER_ASYNC` | Desktop sync/async timers (`board_config`) |
| `PYDISPLAY_LV_ROTATION` | Optional `0`/`90`/`180`/`270` applied to `display_drv.rotation` before `display_driver` import |

The UI shows autodetected **runtime**, **OS**, **display** driver class, **timer** backend, **mode** (`sync`/`async`), and **LVGL** version, plus a seconds counter, spinning arc, and tap button.

### Automated kit mode

```bash
cd src
PYDISPLAY_TIMER_ASYNC=0 .venv/bin/python examples/lv_test_timer.py kit
PYDISPLAY_TIMER_ASYNC=1 .venv/bin/python examples/lv_test_timer.py kit
PYDISPLAY_LV_ROTATION=90 PYDISPLAY_TIMER_ASYNC=0 .venv/bin/python examples/lv_test_timer.py kit
```

Kit mode runs a timed LVGL timer + input check, prints a `KIT_RESULT=` JSON line on stdout, then quits. Prefer [`tools/lv_timer_test_kit.py`](https://github.com/PyDevices/pydisplay/blob/main/tools/lv_timer_test_kit.py) to drive sync/async across desktop runtimes.

### Desktop test suite

[`tools/run_desktop_lv_tests.py`](https://github.com/PyDevices/pydisplay/blob/main/tools/run_desktop_lv_tests.py) runs the kit across **five desktop Python+LVGL executables** in sequence (ten subprocess runs total — `sync` and `async` per runtime).

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

For the full desktop matrix (micropython, circuitpython, cpython-venv, micropython.exe, python.exe × sync/async), use [`tools/lv_timer_test_kit.py`](https://github.com/PyDevices/pydisplay/blob/main/tools/lv_timer_test_kit.py):

```bash
python tools/lv_timer_test_kit.py
python tools/lv_timer_test_kit.py --only python.exe --modes sync
python tools/lv_timer_test_kit.py --only cpython-venv --modes sync async
```

The table shows the timer backend in each cell (e.g. `librt.Timer, ok` / `_async_timer, ok`).

[`tools/run_desktop_lv_tests.py`](https://github.com/PyDevices/pydisplay/blob/main/tools/run_desktop_lv_tests.py) is a shorter wrapper: same runtimes, **sync** and **async**, with strict click checks.

## Next

- [Architecture](../concepts/architecture.md)
- [Events](../concepts/events.md)
- [API reference → displaysys](../reference/overviews/displaysys.md)
