# LVGL

Use pydisplay as the display and input layer for [LVGL on MicroPython](https://github.com/lvgl/lv_micropython).

## Walkthrough

### 1. Install minimum pydisplay packages

--8<-- "_snippets/minimum-mip.md"

Or use [installer.py](../installation/installer.md) for a one-shot setup.

### 2. Build or obtain LVGL MicroPython firmware

Follow upstream [lv_micropython](https://github.com/lvgl/lv_micropython) for your board. pydisplay supplies the flush and input glue via `board_config.py`; LVGL supplies the UI toolkit.

### 3. Wire board_config to LVGL

Your `board_config.py` should expose:

- `display` — pydisplay driver with `blit_rect`, dimensions, rotation
- Touch broker — `eventsys` broker that enqueues touch/mouse events

Connect LVGL's display flush callback to copy LVGL's draw buffer through `display.blit_rect` (or the pattern documented in lv_micropython for your port).

With [`display_driver`](../../src/add_ons/display_driver.py), LVGL input is wired automatically: each indev `read_cb` polls the broker's queue device via virtual touch/encoder/keypad devices. **Do not call `broker.poll()` in your LVGL main loop** — `lv.task_handler()` (driven by `lv_utils` + multimer) already drains input. Calling both competes for the same event queue and breaks clicks. Window-close (`QUIT`) is handled on the same path inside `QueueDevice.poll()`.

### 4. Run the touch test example

Install examples package, then on device:

```python
import lib.path  # development layout only
import lv_touch_test
```

Requires LVGL-enabled firmware. See `src/examples/lv_touch_test.py` in the repo.

### 5. Faster ESP32 buses

For production ESP32 projects, consider [kdschlosser's lvgl_micropython](https://github.com/kdschlosser/lvgl_micropython) C drivers wired through `BusDisplay`.

## Wokwi minimum project

Try displaysys + eventsys without LVGL first: [Wokwi minimum](../guides/wokwi.md) ([hosted](https://wokwi.com/projects/404248867674669057)).

## Helper add-ons

`src/add_ons/lv_utils.py` — LVGL event loop helper (requires `multimer`).

Set **`TIMER_ASYNC`** in `board_config.py` to choose the timer backend:

| `TIMER_ASYNC` | Use when |
|---------------|----------|
| `False` (default) | MCU, MicroPython unix, CPython Linux — default `multimer.Timer` |
| `True` | PyScript and other asyncio-native apps — `multimer.aio.Timer` |

[`display_driver`](../../src/add_ons/display_driver.py) passes this to `lv_utils.event_loop(asynchronous=TIMER_ASYNC)`.

When **`TIMER_ASYNC = True`**, `display_driver` disables SDL's sync `auto_refresh` timer and calls `display.show()` from the aio LVGL refresh loop instead. CircuitPython's default `multimer.Timer` uses a background thread and requires `run_queued()` — which an asyncio app does not call — so the window would never be presented otherwise.

On CPython Win/mac (`TIMER_ASYNC = False`), call **`multimer.run_queued()`** from your main loop when using threaded timer backends — see [multimer](../concepts/multimer.md).

Override before import:

```python
import board_config
board_config.TIMER_ASYNC = True
import display_driver
```

## Timer test examples

Three scripts share the same UI via `lv_test_timer_common.build_ui()` and differ only in how multimer drives LVGL ticks:

| Script | When to run |
|--------|-------------|
| [`lv_test_timer_sync.py`](../../src/examples/lv_test_timer_sync.py) | MCU, MP-unix, CPython Linux — no main loop; **exits** on queued-only platforms |
| [`lv_test_timer_queued.py`](../../src/examples/lv_test_timer_queued.py) | CPython Win/mac — `run_queued()` drain loop only |
| [`lv_test_timer_async.py`](../../src/examples/lv_test_timer_async.py) | PyScript / asyncio — `TIMER_ASYNC = True`, deferred `import display_driver`, `await asyncio.sleep(0)` loop |

## Next

- [Architecture](../concepts/architecture.md)
- [Events](../concepts/events.md)
- [API reference → displaysys](../reference/overviews/displaysys.md)
