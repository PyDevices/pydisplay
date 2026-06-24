# Events

Input is unified through [`eventsys`](https://github.com/PyDevices/pydisplay/tree/main/src/lib/eventsys) — event names and device types follow PyGame/SDL2 where possible.

See [Architecture](architecture.md) for how brokers connect to `board_config.py`.

## Poll loop

```mermaid
flowchart LR
  HW[Hardware] --> Dev[Device.read]
  Dev --> Brok[Broker queue]
  Brok --> Poll[broker.poll]
  Poll --> App[Your handler]
```

Typical main loop:

```python
import board_config
from board_config import broker, display

while True:
    for event in broker.poll():
        if event.type == events.MOUSEBUTTONDOWN:
            ...  # handle touch / click
    display.show()
```

Run [`eventsys_simpletest.py`](https://github.com/PyDevices/pydisplay/blob/main/src/examples/eventsys_simpletest.py) after [first run](../guides/desktop-cpython.md). For a copy-paste app template with clicks, see [**App starter**](../examples/app-starter.md). For rotation and scrolling together, see [**pydisplay_demo**](../examples/pydisplay_demo.md).

## Subscribe vs poll

**Poll** — drain all queued events each frame (most examples).

**Subscribe** — register a callback for specific event types:

```python
def on_touch(event):
    print(event)

broker.subscribe(on_touch, event_types=[events.MOUSEBUTTONDOWN, events.MOUSEBUTTONUP])
```

See [API reference → eventsys.devices.Broker](../reference/eventsys/devices.md).

## Device types

| Device | Source examples |
|--------|-----------------|
| Touch | Touchscreen, mouse |
| Key / Keypad | Keyboard, matrix keypad |
| Encoder | Rotary encoder, mouse scroll wheel |
| Joystick | Game controller |

The same event types fire regardless of physical hardware — develop on desktop with a mouse, deploy with a touchscreen.

## How displays feed the broker

Every display backend feeds the broker the same way — as `eventsys.events`
objects drained through a **`QUEUE`** device — differing only in how that stream
is produced (see [Displays → How displays expose
input](displays.md#how-displays-expose-input)):

- **Desktop** (`SDL2Display`, `PGDisplay`) — module-level `poll()` / `get()`
  drain the native OS event queue and return ready-made `eventsys.events`.
- **Browser / notebook** (`PSDisplay`, `JNDisplay`) — a `PSDevices` / `JNDevices`
  instance captures all available canvas/widget input and returns it via
  `read()`: pointer (`MOUSEMOTION` / `MOUSEBUTTONDOWN` / `MOUSEBUTTONUP`, incl.
  touch and pen on PyScript), wheel (`MOUSEWHEEL`), keyboard (`KEYDOWN` /
  `KEYUP` with SDL-style codes/names/modifiers from the shared keymap in
  `eventsys.keys`), gamepad (`JOY*`, PyScript only), and a `QUIT` from an
  assignable quit chord (default **CTRL+C**).

Either way your handler sees the same `eventsys.events` objects, so application
code does not need to know which backend the active display uses.

## Brokers

`board_config.py` typically sets up brokers that poll hardware and enqueue events:

- Touch brokers read `touch_read_func`
- Keypad brokers scan GPIO
- Encoder brokers count steps

Use polling in your main loop or integrate with a GUI library's event loop.

## Custom device types

`eventsys.custom_type()` registers application-specific event classes. See [API reference → eventsys.custom_type](../reference/eventsys/index.md).

## Next

- [App starter](../examples/app-starter.md) — copy-paste app boilerplate
- [Displays](displays.md)
- [ESP32 quick start](../guides/esp32-board.md)
- [PyScript asyncio](../guides/pyscript-asyncio.md) — async poll loops

## API reference

[API reference (core)](../reference/) → `eventsys`.
