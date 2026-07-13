# 🎨 App starter

Copy one of the scripts below to start your first pydisplay app. Each is a single file that uses only **`src/lib`** modules — no `add_ons`, no `tft_config`, no `displaybuf`.

| Use this | When you want… |
|----------|----------------|
| **App starter** (this page) | A minimal template: draw the UI, handle clicks, `runtime.run_forever()` |
| [**pydisplay_demo**](pydisplay_demo.md) | A feature tour: rotation, hardware scrolling, buffered text, timers |

## Prerequisites

- A working [board config](../hardware/board-configs.md) on your path (from a [full clone](../installation/full-clone.md) or MIP install).
- In a development clone, use `import lib.path` before importing your script so `lib/` and `examples/` are on `sys.path`.

Save the boilerplate as `main.py` (or any name you prefer) and run it from the REPL or as your device's entry point.

## Boilerplate

One file for every host. Build the UI, subscribe callbacks, then `runtime.run_forever()`.
The runtime auto-service dispatches input and QUIT — do **not** call `runtime.poll()`
from an `on_tick` callback. Pass `async_=runtime.timer_async` to `on_tick` so async
hosts do not arm a sync timer before the loop is running.

```python
"""
my_app.py — starting point for a pydisplay app.

Copy and rename to build your own project. Uses board_config, graphics,
and eventsys only.
"""

from board_config import display_drv, runtime
from graphics import Area

# --- customize: colors and layout ---
BG = 0
BTN = 0xF800       # red
BTN_ON = 0x07E0    # green

button = None
pressed = False


def redraw():
    global button
    w, h = display_drv.width, display_drv.height
    display_drv.fill(BG)
    color = BTN_ON if pressed else BTN
    button = Area(display_drv.fill_rect(w // 2 - 50, h // 2 - 25, 100, 50, color))
    display_drv.show()


def on_click(e):
    global pressed
    if button is not None and button.contains(e.pos):
        pressed = not pressed
        redraw()


redraw()
runtime.on(runtime.events.MOUSEBUTTONDOWN, on_click)
runtime.run_forever()
```

## Hit testing and `graphics.Area`

The boilerplate imports `Area` from `graphics` **only for hit-testing**. `display_drv.fill_rect(...)` returns an `(x, y, w, h)` tuple; wrapping it in `Area` lets you write `button.contains(e.pos)` instead of inline coordinate math.

`displaysys` and `eventsys` do not depend on `graphics`. If you want a stack with no `graphics` import — or you install only those packages — keep the tuple from `fill_rect` and test clicks directly:

```python
# displaysys + eventsys only — no graphics import
button = None  # (x, y, w, h)


def redraw():
    global button
    w, h = display_drv.width, display_drv.height
    display_drv.fill(BG)
    color = BTN_ON if pressed else BTN
    button = display_drv.fill_rect(w // 2 - 50, h // 2 - 25, 100, 50, color)
    display_drv.show()


def hit(rect, pos):
    x, y, w, h = rect
    px, py = pos
    return x <= px < x + w and y <= py < y + h


def handle_event(e):
    global pressed
    if e.type == eventsys.MOUSEBUTTONDOWN:
        if hit(button, e.pos):
            pressed = not pressed
            redraw()
```

Stick with `from graphics import Area` when you also use rectangle helpers from `graphics` — union (`area1 + area2`), clip, inset, or dirty rects returned by `graphics` draw functions. See [Drawing and fonts](../concepts/drawing-and-fonts.md).

## Run it

From a [full clone](../installation/full-clone.md) with `board_config` on your path, paste the script into `src/main.py` (or run from the REPL):

```python
import lib.path   # adds lib/, examples/ to sys.path (dev clone only)
# import my_app   # or paste/run your saved script
```

Desktop (SDL board config):

```bash
cd src
PYTHONPATH=../board_configs/sdldisplay:lib micropython -i lib/path.py
```

On MCU, install the matching [board config](../hardware/board-configs.md), copy or symlink it as `board_config.py`, and run `main.py` from flash or the REPL.

**Interact:** tap or click the centered rectangle — it toggles between red and green.

## Walkthrough

### `redraw()`

Clears the screen, draws one clickable rectangle, and calls `display_drv.show()` once. `fill_rect` returns `(x, y, w, h)`; the boilerplate wraps that in `Area` for `button.contains(event.pos)`.

Recreate `Area` objects whenever you change layout (same pattern as real apps with moving widgets).

### `on_click` / event callbacks

Per-event handling stays in callbacks registered with `runtime.on(...)`. The
starter handles `MOUSEBUTTONDOWN` only. Add more `runtime.on` subscriptions for
keys, encoders, and other devices — see [Events](../concepts/events.md).

### Main loop

`runtime.run_forever()` keeps the app live on every host — see
[Runtime](../concepts/runtime.md) and [multimer](../concepts/multimer.md).
PyScript and Jupyter always construct `runtime` with `timer_async=True`; desktop
defaults to sync unless `PYDISPLAY_TIMER_ASYNC=1` is set before `board_config` loads.

## Customize

1. **Rename** the file and module docstring.
2. **Layout** — add more `Area` regions, sprites, or shapes in `redraw()`.
3. **Text** — for labels and lists, use `Font` + `FrameBuffer` + `blit_rect` ([Drawing and fonts](../concepts/drawing-and-fonts.md), [`font_simpletest.py`](https://github.com/PyDevices/pydisplay/blob/main/src/examples/font_simpletest.py)).
4. **Timers** — use `runtime.on_tick(callback, period=…, async_=runtime.timer_async)`; see [multimer](../concepts/multimer.md) and [**pydisplay_demo**](pydisplay_demo.md).

!!! tip "Next steps beyond this template"
    - **Rotation and hardware scroll** — [pydisplay_demo](pydisplay_demo.md)
    - **Event types and runtime** — [Events](../concepts/events.md), [Runtime](../concepts/runtime.md)
    - **All example scripts** — [Examples catalog](index.md)

## Related docs

- [Board configs](../hardware/board-configs.md) — choose and customize `board_config.py`
- [Architecture](../concepts/architecture.md) — how board_config, displaysys, and eventsys fit together
- [pydisplay_demo](pydisplay_demo.md) — flagship feature demo (rotation, scroll, buffered text)
- [Examples catalog](index.md) — full list of scripts
