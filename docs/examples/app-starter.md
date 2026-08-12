# 🎨 App starter

Copy the script below to start your first app with the published product packages
and pydevices-examples's small `app_runtime` helper.

| Use this | When you want… |
|----------|----------------|
| **App starter** (this page) | A minimal template: draw the UI, handle clicks, `runtime.run_forever()` |
| [**pydevices_demo**](pydevices-demo.md) | A feature tour: rotation, hardware scrolling, buffered text, timers |

## Prerequisites

- A working [board config](https://pydevices.github.io/pydevices/board-configs.html) on your path.
- Product packages installed from TestPyPI/MIP, or a sibling `pydevices` development checkout.
- `src/utils` on the path so `app_runtime` resolves.

Save the boilerplate as `main.py` (or any name you prefer) and run it from the REPL or as your device's entry point.

## Boilerplate

One file for every host. Build the UI, subscribe callbacks, then `runtime.run_forever()`.
The runtime auto-service dispatches input and QUIT — do **not** call `runtime.poll()`
from an `on_tick` callback. Pass `async_=runtime.timer_async` to `on_tick` so async
hosts do not arm a sync timer before the loop is running.

```python
"""
my_app.py — starting point for a pydevices-examples app.

Copy and rename to build your own project. Uses board_config, pygraphics,
and the optional eventsys coordinator selected by app_runtime.
"""

from board_config import display_drv
from app_runtime import runtime
from pygraphics import Area

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

## Hit testing and `pygraphics.Area`

The boilerplate imports `Area` from `pygraphics` **only for hit-testing**. `display_drv.fill_rect(...)` returns an `(x, y, w, h)` tuple; wrapping it in `Area` lets you write `button.contains(e.pos)` instead of inline coordinate math.

`displaydev` and `eventsys` do not depend on `pygraphics`. If you want a stack with no `pygraphics` import — or you install only those packages — keep the tuple from `fill_rect` and test clicks directly:

```python
# displaydev + eventsys only — no pygraphics import
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
    if e.type == runtime.events.MOUSEBUTTONDOWN:
        if hit(button, e.pos):
            pressed = not pressed
            redraw()
```

Stick with `from pygraphics import Area` when you also use rectangle helpers from `pygraphics` — union (`area1 + area2`), clip, inset, or dirty rects returned by `pygraphics` draw functions. See [Drawing and fonts](../concepts/drawing-and-fonts.md).

## Run it

From a [full clone](../installation/full-clone.md), save the boilerplate as `lib/main.py`, then set `PYTHONPATH`/`MICROPYPATH`, `cd lib`, and run it directly — no path bootstrap needed:

```bash
cd pydevices-examples/lib
PYTHONPATH=.:utils ../.venv/bin/python main.py
```

With sibling source checkouts instead of installed packages:

```bash
cd pydevices-examples/lib
export PYTHONPATH=.:utils:../../pydevices/lib:../../pydevices/drivers/display
python3 main.py
```

On MCU, install the matching [board config](https://pydevices.github.io/pydevices/board-configs.html), the optional `eventsys` package, and pydevices-examples's `utils` package, then run `main.py` from flash or the REPL. For fallback path handling, see [Utils path setup](../utils.md#path-setup).

**Interact:** tap or click the centered rectangle — it toggles between red and green.

## Walkthrough

### `redraw()`

Clears the screen, draws one clickable rectangle, and calls `display_drv.show()` once. `fill_rect` returns `(x, y, w, h)`; the boilerplate wraps that in `Area` for `button.contains(event.pos)`.

Recreate `Area` objects whenever you change layout (same pattern as real apps with moving widgets).

### `on_click` / event callbacks

Per-event handling stays in callbacks registered with `runtime.on(...)`. The
starter handles `MOUSEBUTTONDOWN` only. Add more `runtime.on` subscriptions for
keys, encoders, and other devices — see [Events](https://pydevices.github.io/pydevices/eventsys.html).

### Main loop

`runtime.run_forever()` keeps the app live on every host — see
[Runtime](https://pydevices.github.io/pydevices/application-runtime.html) and [multimer](https://pydevices.github.io/pydevices/multimer.html).
PyScript and Jupyter board configs export `timer_async=True`; desktop defaults
to sync unless `PYDEVICES_TIMER_ASYNC=1` is set before the coordinator is created.

## Customize

1. **Rename** the file and module docstring.
2. **Layout** — add more `Area` regions, sprites, or shapes in `redraw()`.
3. **Text** — for labels and lists, use `Font` + `FrameBuffer` + `blit_rect` ([Drawing and fonts](../concepts/drawing-and-fonts.md), [`font_simpletest.py`](https://github.com/PyDevices/pydevices-examples/blob/main/lib/examples/font_simpletest.py)).
4. **Timers** — use `runtime.on_tick(callback, period=…, async_=runtime.timer_async)`; see [multimer](https://pydevices.github.io/pydevices/multimer.html) and [**pydevices_demo**](pydevices-demo.md).

!!! tip "Next steps beyond this template"
    - **Rotation and hardware scroll** — [pydevices_demo](pydevices-demo.md)
    - **Event types and runtime** — [Events](https://pydevices.github.io/pydevices/eventsys.html), [Runtime](https://pydevices.github.io/pydevices/application-runtime.html)
    - **All example scripts** — [Examples catalog](index.md)

## Related docs

- [Board configs](https://pydevices.github.io/pydevices/board-configs.html) — choose and customize `board_config.py`
- [Architecture](https://pydevices.github.io/pydevices/architecture.html) — how board_config, displaydev, and eventsys fit together
- [pydevices_demo](pydevices-demo.md) — flagship feature demo (rotation, scroll, buffered text)
- [Examples catalog](index.md) — full list of scripts
