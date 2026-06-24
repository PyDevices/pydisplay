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

Jupyter Notebook output via an interactive `ipywidgets` image when touch is enabled (`JNDevices` + `ipyevents`). Mouse clicks map to touch events. Config: `board_configs/jndisplay/`.

### PSDisplay

PyScript browser canvas. Touch only. Config: `board_configs/psdisplay/`. See [PyScript](../guides/pyscript.md).

### EPaperDisplay

Planned — community help wanted.

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
