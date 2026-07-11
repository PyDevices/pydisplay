# Runtime and board_config

Every pydisplay app expects a **`board_config.py`** on `sys.path` that exports:

| Symbol | Required | Role |
|---|---|---|
| `display_drv` | yes | Display backend from [displaysys](displays.md) |
| `runtime` | when `display_drv.needs_refresh` | [eventsys](events.md) `Runtime` — shared timer, optional input, quit lifecycle |

**`runtime = None`** is allowed only on MCU boards whose display does **not** need periodic presentation (`needs_refresh` is false): bus displays, e-paper, pixel grids driven explicitly by the app. Hosted backends (SDL, pygame, PyScript, Jupyter) always export a `Runtime`.

## Quick start — hosted desktop

```python
from sdldisplay import SDLDisplay, get_events
import eventsys

display_drv = SDLDisplay(width=320, height=480, rotation=0, scale=2.0, title="My app")

runtime = eventsys.Runtime(
    display=display_drv,
    host_read=get_events,
)
```

The runtime wires periodic `display_drv.show()` automatically when `display_drv.needs_refresh` is true (~30 FPS by default). No app code calls `on_tick` for refresh.

## Quick start — MCU with touch

```python
import eventsys
from machine import I2C, Pin
from ft6x36 import FT6x36
from st7796 import ST7796

# ... bus, display_drv, touch_drv setup ...

runtime = eventsys.Runtime(
    display=display_drv,
    touch_read=touch_drv.get_positions,
)
```

## Quick start — display-only MCU

```python
import eventsys
from st7789 import ST7789

display_drv = ST7789(...)  # bus display; needs_refresh is False

runtime = None
```

## App loop

```python
from board_config import display_drv, runtime

while runtime is None or not runtime.quit_requested:
    if runtime is not None:
        for event in runtime.poll():
            handle(event)
    draw_frame()
```

Output-only demos that never read input still need `runtime` on hosted boards (for auto-refresh and window quit):

```python
while not runtime.quit_requested:
    draw_frame()
    runtime.poll()
```

## Runtime constructor

```python
eventsys.Runtime(
    display=None,              # duck-typed: show(), quit(), optional needs_refresh
    host_read=None,            # hosted event pump (SDL/pygame/PyScript/Jupyter)
    touch_read=None,           # callable returning touch point(s) or falsy
    touch_rotation_table=None, # optional 4-item rotation mask table
    refresh_period=None,       # ms; None = use DEFAULT_REFRESH_MS when needs_refresh
    timer_async=False,         # True for PyScript / Jupyter; desktop default in lib/board_config
)
```

### `timer_async` in `src/lib/board_config.py`

The shipped default config sets `timer_async` per host:

| Host | Value |
|------|-------|
| PyScript | `True` |
| Jupyter | `True` |
| PG/SDL desktop | `False`, or `env_bool("PYDISPLAY_TIMER_ASYNC", False)` |

Set **`PYDISPLAY_TIMER_ASYNC`** in the process environment before
`board_config` is imported to run desktop examples with asyncio timers (LVGL
async path, cross-runtime matrix columns). See
[`displaysys.env_bool`](../../src/lib/displaysys/__init__.py) and [Board configs — default](../hardware/board-configs.md#default-config).

On SDL2 / Win32 sync timer hosts (`micropython.exe`, and similar), display
refresh is **deferred until the first `runtime.poll()`** so importing
`board_config` in a REPL does not start an SDL timer without a drain loop.

Additional inputs after construction:

```python
runtime.add_keypad(read=buttons.read)
runtime.add_joystick(joystick_driver=drv)
runtime.add_encoder(read=pos_read, button_read=btn_read, button=2)
```

Bare `Runtime()` with no arguments is valid for tests and custom wiring via `register()`.

## Touch read contract

Pass a callable as `touch_read=` (typically the touch driver's
`get_positions`). Each poll, the runtime calls it once and maps the result to
mouse events.

| Return value | Meaning |
|---|---|
| falsy (`None`, `()`, `[]`) | no touch — emits `MOUSEBUTTONUP` if a press was active |
| `(x, y)` | touch at pixel coordinates |
| `(x, y, pressed)` | same; extra fields ignored |
| `[(x, y), …]` | first point used (multi-touch not surfaced yet) |

Coordinates are in **display pixel space** before rotation mapping. When the
default table is wrong for your panel, pass `touch_rotation_table=` — a
4-tuple of rotation masks (one per 90° step). See [Events — touch](events.md#built-in-devices).

Touch drivers live under `drivers/touch/`. OSError from `touch_read` is treated
as no touch for that poll.

## Display refresh takeover (LVGL, games)

GUI layers that present frames themselves can pause runtime-driven refresh:

```python
claim = runtime.claim_display_refresh()
try:
    ...  # present frames yourself
finally:
    claim.release()
```

Or use the context manager:

```python
with runtime.display_refresh_paused():
    run_game()
```

## Quit lifecycle

On `QUIT`, the runtime runs (in order): `before_quit` hook (if set) → `display.quit()` → `stop_timer()`. Set `runtime.before_quit` for LVGL shutdown before the display is released.

`runtime.quit_requested` becomes true after the first quit and stays true (sticky flag).

## Package boundaries

- **displaysys** declares `needs_refresh` (boolean only); no timer code.
- **eventsys** owns `DEFAULT_REFRESH_MS` and the shared timer; duck-types `display` without importing displaysys.
- **board_config** is the only place that names both packages together.

See also: [Events](events.md), [Architecture](architecture.md), [Board configs](../hardware/board-configs.md).
