# Displays

pydisplay provides several display driver classes. All expose a drawing surface compatible with MicroPython's `framebuf` API.

See [Architecture](architecture.md) for how drivers connect to `board_config.py`.

## Pick a driver

| Your target | Driver class | Board config example |
|-------------|--------------|----------------------|
| MicroPython MCU (SPI/I80) | `BusDisplay` | `board_configs/busdisplay/spi/...` |
| CPython / MicroPython Unix desktop | `SDL2Display` | `board_configs/sdldisplay/` |
| Windows / Chromebook (PyGame easier) | `PGDisplay` | `board_configs/pgdisplay/` |
| CircuitPython RGB / USB video | `FBDisplay` | varies |
| Jupyter notebook | `JNDisplay` | `board_configs/jndisplay/` |
| PyScript browser | `PSDisplay` | `board_configs/psdisplay/` |

Install the matching [board config](../hardware/board-configs.md) — it constructs the driver for you.

## Display classes

### BusDisplay

For microcontrollers on **MicroPython and CircuitPython**.

- MicroPython: uses `spibus` / `i80bus` or community C bus drivers ([lvgl_micropython](https://github.com/kdschlosser/lvgl_micropython)).
- CircuitPython: uses Adafruit FourWire / ParallelBus — see [CircuitPython guide](../platforms/circuitpython.md).

### SDL2Display

Preferred desktop backend (CPython / MicroPython Unix). Uses an SDL texture as GRAM. Config: `board_configs/sdldisplay/`.

### PGDisplay

Optional desktop backend using PyGame surfaces. Easier on Windows; avoids some SDL glitches on Chromebooks. Config: `board_configs/pgdisplay/`.

### FBDisplay

Works with CircuitPython `framebufferio.FramebufferDisplay` — dotclock (RGB), USB Video, RGB Matrix.

USB Video lets a board stream the framebuffer as a USB webcam (RP2040; host support varies).

### JNDisplay

Jupyter Notebook output via an interactive `ipywidgets` image when touch is enabled (`JNTouch` + `ipyevents`). Mouse clicks map to touch events. Config: `board_configs/jndisplay/`.

### PSDisplay

PyScript browser canvas. Touch only. Config: `board_configs/psdisplay/`. See [PyScript](../guides/pyscript.md).

### EPaperDisplay

Planned — community help wanted.

## How displays expose input

Display backends do not handle input the same way, because the platforms they
run on do not offer the same input capabilities. There are **two families**,
and which one a backend belongs to determines how its `board_config.py` wires
input into [`eventsys`](events.md).

| Family | Backends | Driver exposes | eventsys device | Reports |
|--------|----------|----------------|-----------------|---------|
| **Native event queue** | `SDL2Display`, `PGDisplay` | module-level `poll()` / `get()` returning `eventsys.events` objects | `QUEUE` | mouse motion/buttons, wheel, keyboard, window-close (QUIT) |
| **Single-pointer** | `JNDisplay`, `PSDisplay` | a touch helper class (`JNTouch` / `PSTouch`) with `get_mouse_pos()` | `TOUCH` | left-button "touch" only (synthesized MOUSEBUTTONDOWN / MOUSEMOTION / MOUSEBUTTONUP) |

### Native event queue (SDL2, PyGame)

SDL2 and PyGame provide a real OS event queue. The driver module drains it and
converts each event to an `eventsys.events` object, then `board_config.py`
registers a `QUEUE` device:

```python
from displaysys.sdldisplay import SDLDisplay, poll
from eventsys import devices

display_drv = SDLDisplay(...)
broker = devices.Broker()
broker.create_device(type=devices.types.QUEUE, read=poll, data=display_drv)
```

This is the richest model — keyboard, mouse wheel, all mouse buttons, and the
window-close event all flow through one device.

### Single-pointer (Jupyter, PyScript)

Jupyter and PyScript only expose pointer events on a single widget/canvas, so
each provides a small helper class that tracks the current pressed position via
`get_mouse_pos()`. `board_config.py` registers it as a `TOUCH` device, and
`eventsys` synthesizes button-1 press/move/release events from the polled
position (and applies touch rotation):

```python
from displaysys.psdisplay import PSDisplay, PSTouch
from eventsys import devices

display_drv = PSDisplay("display_canvas", width, height)
broker = devices.Broker()
touch_drv = PSTouch("display_canvas")
broker.create_device(type=devices.types.TOUCH, read=touch_drv.get_mouse_pos, data=display_drv)
```

These backends cannot offer the full queue model because the platform has no
equivalent keyboard/window event stream — the single-pointer helper is the most
they can support.

## Canvases

Anything you can draw on implements the framebuf API:

- The display itself
- `framebuf` bytearrays
- `bmp565.BMP565` bitmap files
- `displaybuf.DisplayBuffer` (see [add-ons](../add-ons.md))

## Timing

pydisplay does not include a task scheduler. Options:

- **`asyncio`** — works on CPython, MicroPython, and PyScript (required there)
- **[multimer](multimer.md)** — cross-platform timers; default `Timer` for sync/threaded loops
- **[multimer.aio](multimer.md#multimeraio--asyncio-timers)** — opt-in asyncio timers for async/PyScript apps

## Vertical scrolling

Many drivers expose **ILI9341-style** vertical scroll: a top fixed band (TFA), a scrollable middle (VSA), and a bottom fixed band (BFA). You define regions with `set_vscroll(tfa, bfa)` or `vscrdef`, then move content with the `vscroll` property (wrapper around `vscsad`).

The [**pydisplay_demo**](../examples/pydisplay_demo.md) guide explains this model with diagrams, covers drawing at `vscroll = 0` during redraw, and shows auto-scroll with `multimer`.

Related examples: [`scroll_touch_test.py`](https://github.com/PyDevices/pydisplay/blob/main/src/examples/scroll_touch_test.py) (touch Up/Down), [`eventsys_encoder_test.py`](https://github.com/PyDevices/pydisplay/blob/main/src/examples/eventsys_encoder_test.py) (encoder).

## Rotation

BusDisplay uses CircuitPython-style rotation degrees (`0`, `90`, `180`, `270`).

Known issues: Unix SDL rotation clears the screen; scrolling while rotated has edge cases on desktop and MCU — see [roadmap](https://github.com/PyDevices/pydisplay#roadmap).

## Next

- [Events](events.md)
- [Drawing and fonts](drawing-and-fonts.md)
- [Display drivers (chips)](../hardware/display-drivers.md)

## API reference

[API reference (core)](../reference/) → `displaysys`.
