# eventsys

Cross-platform input events with PyGame/SDL2-style types. One import covers the runtime, built-in devices, event constants, and key codes.

For board wiring, auto-refresh, and the `runtime = None` rule, see **[Runtime](runtime.md)**.

## Quick start — poll loop

```python
import eventsys

runtime = eventsys.Runtime()
keypad = eventsys.KeypadDevice(read=lambda: pressed_keys)  # set of key codes
runtime.register(keypad)

while True:
    for event in runtime.poll():  # always a list — safe to iterate
        if event.type == eventsys.KEYDOWN:
            print("down", event.key)
        elif event.type == eventsys.QUIT:
            break
```

## Quick start — subscribe

```python
import eventsys

runtime = eventsys.Runtime()

def on_key(event):
    print(event)

runtime.on(eventsys.KEYDOWN, on_key)
runtime.on([eventsys.KEYDOWN, eventsys.KEYUP], on_key)
runtime.on_device(eventsys.KEYPAD, on_key)
```

## Quick start — async

Pair eventsys with [multimer](multimer.md) on asyncio-native hosts:

```python
import eventsys
import multimer

runtime = eventsys.Runtime()

async def main():
    while True:
        for event in runtime.poll():
            handle(event)
        await multimer.sleep_ms(0)

multimer.run(main)
```

Or subscribe and let the runtime auto-service drive the app:

```python
runtime.on(runtime.events.MOUSEBUTTONDOWN, handle)
runtime.run_forever()
```

## Poll vs subscribe

| Pattern | When to use |
|---------|-------------|
| **Poll** | Main loop owns flow; inspect every event each frame. |
| **`runtime.on()`** | React to specific event types without a big `if` chain. |
| **`runtime.on_device()`** | Handle all events from touch, keypad, joystick, etc. |

`runtime.poll()` **always** returns a list (possibly empty). It never returns `None`.

## Built-in devices

| Device | Input contract |
|--------|----------------|
| `HostEventsDevice` | `read()` returns ready-made events (desktop SDL/PyGame bridge). |
| `TouchDevice` | `read()` returns `(x, y, pressed)`; maps to mouse events. |
| `KeypadDevice` | `read()` returns a `set` of pressed key codes. |
| `EncoderDevice` | `read()` returns scroll delta / button state. |
| `JoystickDevice` | `joystick_driver` with PyGame-style `get_axis`, `get_button`, `get_hat`, … |

Register devices with `runtime.register(dev)` or the constructor helpers
(`Runtime(..., touch_read=...)`, `runtime.add_keypad(read=...)`, etc.).

### Joystick

```python
import eventsys

class MyDriver(eventsys.JoystickDriver):
    def get_instance_id(self):
        return 0
    # implement get_numaxes, get_axis, get_numbuttons, get_button, …

joy = eventsys.JoystickDevice(
    joystick_driver=MyDriver(),
    emulate_digital=[(0, 1)],  # optional: analog axes → hat motion
)
runtime.register(joy)
runtime.on_device(eventsys.JOYSTICK, lambda e: print(e))
```

## Quit handling

When constructed with `display=`, the runtime handles quit implicitly: on
`events.QUIT` it runs `before_quit` (if set), then `display.quit()`, then
stops the shared timer. Set `runtime.before_quit` for LVGL teardown before the
display is released.

```python
runtime.before_quit = _lvgl_shutdown
```

Use **`runtime.quit_requested`** in output-only loops that do not dispatch
events (the auto-service still handles host QUIT when you call `poll` or run
`run_forever`):

```python
from board_config import display_drv, runtime

while not runtime.quit_requested:
    draw_frame()
    # Prefer runtime.run_forever() for interactive apps; poll only when you
    # own a custom frame loop and need to drain events yourself.
```

Canonical interactive apps subscribe callbacks and stay alive with:

```python
runtime.on(runtime.events.MOUSEBUTTONDOWN, handle)
runtime.run_forever()
```

`display_drv.quit()` only releases resources (REPL-safe); your loop must still
exit when `runtime.quit_requested` becomes true or you handle `events.QUIT`.

## Custom events and devices

```python
import eventsys

eventsys.register_event(types={"MINE": None}, classes={"Mine": "type a b"})
eventsys.register_device("MYPAD", [eventsys.KEYDOWN, eventsys.KEYUP])
```

Use `eventsys.capabilities()` to inspect the dialect and built-in device list.

## FAQ

**No events arrive** — call `runtime.poll()` frequently in your main loop.

**Touch coordinates wrong** — set `TouchDevice.rotation_table` for your panel rotation.

**Joystick hats from analog sticks** — pass `emulate_digital=[(axis_x, axis_y), …]`.

## pydisplay integration

pydisplay wires a `HostEventsDevice` and implicit quit cleanup in
`board_config.py` via `eventsys.Runtime(...)`. Display-only MCU configs set
`runtime = None`. See [Runtime](runtime.md), [Architecture](architecture.md),
and [Displays](displays.md).

## Next

- [multimer](multimer.md) — timers and async main loops
- [Displays](displays.md) — how backends feed the runtime
- [App starter](../examples/app-starter.md)

## API reference

[API reference (core)](../reference/) → `eventsys`.
