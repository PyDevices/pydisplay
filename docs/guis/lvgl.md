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

Map LVGL input devices to pydisplay touch events from `broker.poll()`.

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

`src/add_ons/lv_utils.py` — LVGL event loop helper (requires `multimer`; uses `multimer.aio` for async mode).

## Next

- [Architecture](../concepts/architecture.md)
- [Events](../concepts/events.md)
- [API reference → displaysys](../reference/overviews/displaysys.md)
