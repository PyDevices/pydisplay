# Displays

pydisplay provides several display driver classes. All expose a drawing surface compatible with MicroPython's `framebuf` API.

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

Jupyter Notebook output. No input devices yet. Config: `board_configs/jndisplay/`.

### PSDisplay

PyScript browser canvas. Touch only. Config: `board_configs/psdisplay/`. See [PyScript](../platforms/pyscript.md).

### EPaperDisplay

Planned — community help wanted.

## Canvases

Anything you can draw on implements the framebuf API:

- The display itself
- `framebuf` bytearrays
- `bmp565.BMP565` bitmap files
- `displaybuf.DisplayBuffer` (see add_ons)

## Timing

pydisplay does not include a task scheduler. Options:

- **`asyncio`** — works on CPython, MicroPython, and PyScript (required there)
- **[multimer](../installation/index.md)** — scheduled callbacks on CPython and MicroPython (not CircuitPython)

## Rotation

BusDisplay uses CircuitPython-style rotation degrees (`0`, `90`, `180`, `270`).

Known issues: Unix SDL rotation clears the screen; scrolling while rotated has edge cases on desktop and MCU — see [roadmap](https://github.com/PyDevices/pydisplay#roadmap).

## API reference

Auto-generated docs: [Package Reference](../reference/) → `displaysys`.
