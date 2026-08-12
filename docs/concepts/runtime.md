# Runtime and board config

Every application needs a `board_config.py` on `sys.path` that describes its
hardware or host. The board config exports hardware capabilities; the
application decides which coordinator, if any, to instantiate.

## Board-config contract

| Symbol | Required | Role |
|---|---|---|
| `display_drv` | yes for display apps | Display interface from `displaydev` |
| `host_read` | hosted input only | Callable that returns host events |
| `touch_read` | touch boards only | Callable that returns contact points |
| `touch_rotation_table` | optional | Four rotation masks for touch coordinates |
| `keypad_read` | optional | Keypad reader |
| `encoder_read` / `encoder_button_read` | optional | Encoder readers |
| `joystick_driver` / `emulate` | optional | Joystick input and optional emulation mapping |
| `timer_async` | optional | Host preference for async timing |

Board configs do not import `eventsys` and do not export `runtime`.

## Non-LVGL examples

pydevices-examples's examples opt into the optional event traffic controller through the
application helper:

```python
from board_config import display_drv
from app_runtime import runtime

runtime.run_forever()
```

`app_runtime` calls `eventsys.Runtime.from_board_config(board_config)` and adds
only gallery/example test behavior. Reusable `eventsys` remains independent of
pydevices-examples.

For your own app, instantiate the coordinator directly:

```python
import board_config
import eventsys

runtime = eventsys.Runtime.from_board_config(board_config)
```

You may also provide overrides:

```python
runtime = eventsys.Runtime.from_board_config(
    board_config,
    refresh_period=16,
    timer_async=True,
)
```

## LVGL applications

LVGL supplies its own coordinator:

```python
from display_driver import runtime
```

That implementation bridges LVGL to `displaydev` and `multimer`, owns LVGL
tick/task handling and input-device adapters, and does not import `eventsys`.

## Direct constructor

```python
eventsys.Runtime(
    display=None,
    host_read=None,
    touch_read=None,
    touch_rotation_table=None,
    refresh_period=None,
    timer_async=False,
)
```

Bare `Runtime()` is valid for custom wiring. Additional devices can be attached
after construction:

```python
runtime.add_keypad(read=buttons.read)
runtime.add_joystick(joystick_driver=drv)
runtime.add_encoder(read=pos_read, button_read=btn_read, button=2)
```

## App loop

The supplied coordinator can dispatch callbacks and own the loop:

```python
def on_click(event):
    ...


runtime.on(runtime.events.MOUSEBUTTONDOWN, on_click)
runtime.run_forever()
```

Or an application can explicitly poll:

```python
while not runtime.quit_requested:
    for event in runtime.poll():
        handle(event)
    draw_frame()
```

Hosted displays that set `needs_refresh` are presented by the coordinator.
Display-only MCU applications can omit `eventsys` entirely and call
`display_drv.show()` according to their own policy.

## `timer_async`

Board configs publish a neutral `timer_async` preference. Current defaults are:

| Host | Value |
|---|---|
| PyScript / Jupyter | `True` |
| PG/SDL desktop | `False`, optionally overridden by `PYDEVICES_TIMER_ASYNC` |
| MCU board config | selected by that config |

Examples do not read the environment variable directly. The selected
coordinator consumes `board_config.timer_async`; test harnesses can use their
`--timer-async` option.

## Touch read contract

`touch_read` is called once per poll. It returns either a falsy value for no
contacts or a sequence of `(x, y[, id[, …]])` contacts. The runtime maps the
primary contact to mouse-style events and exposes all rotated contacts as
`runtime.touch_dev.points`.

| Return value | Meaning |
|---|---|
| `None`, `()`, or `[]` | no touch; releases an active press |
| sequence of point tuples | current contacts |
| legacy bare `(x, y[, …])` | one contact; supported for compatibility |

Coordinates are panel/pre-rotation coordinates. `touch_rotation_table` maps
them to the active display rotation. New drivers should prefer `read_points()`
returning a sequence, even for one contact.

## Refresh ownership

A GUI layer that presents frames itself can pause eventsys-driven refresh:

```python
with runtime.display_refresh_paused():
    run_game()
```

LVGL does not use this eventsys mechanism: its own coordinator owns presentation
from the outset.

## Quit lifecycle

On `QUIT`, eventsys runs its optional `before_quit` hook, releases the display,
and stops its timer. `runtime.quit_requested` remains true after the first quit.

See [Events](events.md), [Architecture](architecture.md), and
[Board configs](https://pydevices.github.io/pydevices/board-configs.html).
