# Displays

pydisplay provides several display driver classes. All expose a drawing surface compatible with MicroPython's `framebuf` API.

See [Architecture](architecture.md) for how drivers connect to `board_config.py`.

## Pick a driver

| Your target | Driver class | Board config example |
|-------------|--------------|----------------------|
| MicroPython MCU (SPI/I80) | `BusDisplay` | `board_configs/busdisplay/spi/...` |
| CPython / MicroPython Unix desktop | `SDLDisplay` | `board_configs/sdldisplay/` |
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

### SDLDisplay

SDL2 desktop backend (CPython, MicroPython Unix, CircuitPython Unix). Uses an SDL texture as GRAM. It is the default on MicroPython Unix and available on CPython via `board_configs/sdldisplay/`.

SDL2 bindings for **`SDLDisplay`**: native frozen **`usdl2`** when built in, else **`add_ons/usdl2.py`** on ``sys.path``. Build **`usdl2`** from [PyDevices/usdl2](https://github.com/PyDevices/usdl2) for frozen MicroPython and CircuitPython Unix — see [MicroPython — usdl2](../platforms/micropython.md#usdl2-native-sdl2).

### PGDisplay

PyGame desktop backend. The default `board_config.py` selects it first on CPython (it is easier to install on Windows and avoids some SDL glitches on Chromebooks); if PyGame is not installed it falls back to `SDLDisplay`. Config: `board_configs/pgdisplay/`.

### FBDisplay

Works with CircuitPython `framebufferio.FramebufferDisplay` — dotclock (RGB), USB Video, RGB Matrix.

USB Video lets a board stream the framebuffer as a USB webcam (RP2040; host support varies).

### JNDisplay

Jupyter Notebook output via an interactive `ipywidgets` image. Input (mouse, wheel, keyboard) is captured by `JNDevices` (`ipyevents`) and delivered as events. Config: `board_configs/jndisplay/`.

### PSDisplay

PyScript browser canvas. Input (pointer/touch/pen, wheel, keyboard, gamepad) is captured by `PSDevices` and delivered as events. Config: `board_configs/psdisplay/`. See [PyScript](../guides/pyscript.md).

### EPaperDisplay

Planned — community help wanted.

## How displays expose input

All display backends feed input into [`eventsys`](events.md) the same way: as a
stream of `eventsys.events` objects drained through a **`HostEventsDevice`**. They
differ only in *how* that stream is produced, which depends on what each
platform exposes:

| Backends | Input source | Wired via |
|----------|--------------|-----------|
| `SDL2Display`, `PGDisplay` | module-level `get_events()` draining the native OS event queue | `Runtime(..., host_read=get_events)` |
| `JNDisplay`, `PSDisplay` | a `JNDevices` / `PSDevices` instance capturing browser input, drained via `read()` | `Runtime(..., host_read=devices_drv.read)` |

Either way your handler sees the same `eventsys.events` objects, so application
code never needs to know which backend is active.

### Desktop (SDL2, PyGame)

SDL2 and PyGame provide a real OS event queue. The driver module drains it and
converts each event to an `eventsys.events` object:

```python
from displaysys.sdldisplay import SDLDisplay, get_events
import eventsys

display_drv = SDLDisplay(...)
runtime = eventsys.Runtime(display=display_drv, host_read=get_events)
```

Use `poll_event()` only for optional manual single-event checks — not as the
`host_read=` callback (it returns one event, not a list).

Default quit chord on event backends is **CTRL+Q** (`display_drv.quit_chord`);
`HostEventsDevice` applies it when constructed with `display=`. Window-close still
emits `events.QUIT` from SDL/PyGame.

Pointer coordinates use `display_drv.touch_scale` (see `capabilities()` per
backend); `HostEventsDevice` divides mouse events by that scale.

This captures mouse motion/buttons, the wheel, the keyboard, the window-close
(`QUIT`) event, and **joysticks/gamepads** (`JOYAXISMOTION`, `JOYBALLMOTION`,
`JOYHATMOTION`, `JOYBUTTONDOWN`, `JOYBUTTONUP`). Connect controllers before
launching — hot-plugging after startup is not handled.

### Browser / notebook (PyScript, Jupyter)

`PSDevices` (PyScript) and `JNDevices` (Jupyter) capture all available input on
the canvas/widget and turn it into the same `eventsys.events` objects, drained
through `read()`:

```python
from displaysys.psdisplay import PSDevices, PSDisplay
import eventsys

display_drv = PSDisplay("display_canvas", width, height)
devices_drv = PSDevices("display_canvas", display_drv)
runtime = eventsys.Runtime(display=display_drv, host_read=devices_drv.read)
```

Each captures:

- **Pointer** — `MOUSEMOTION` on every move and `MOUSEBUTTONDOWN` /
  `MOUSEBUTTONUP` for any button. On PyScript this uses Pointer Events, so mouse,
  touch, and pen all work (with the `touch` flag set for non-mouse pointers).
- **Wheel** — `MOUSEWHEEL` (also consumed by encoder devices).
- **Keyboard** — `KEYDOWN` / `KEYUP` with SDL-style key codes, names, and
  modifier masks (incl. left/right modifier variants) via the shared keymap in
  `eventsys.keys`.
- **Gamepad** (PyScript only) — `JOYAXISMOTION` / `JOYBUTTONDOWN` /
  `JOYBUTTONUP`, polled from the Gamepad API on each `read()`.
- **Quit** — an assignable key chord emits `events.QUIT` (the equivalent of
  clicking an SDL window's close button; the broker then deinitializes the
  display and exits). It defaults to **CTRL+C**; reassign if the host intercepts
  it:

```python
from eventsys.keys import Keys

devices_drv.quit_chord = (Keys.K_q, Keys.KMOD_CTRL)  # use CTRL+Q instead
```

> **Caveat:** key events require the canvas/widget to be focused (click it
> first), and the notebook/browser front end may consume some keys (arrows,
> space, `Ctrl`/`Cmd` shortcuts) before they reach the helper. This makes
> keyboard input on these backends less reliable than on the desktop SDL/PyGame
> backends.
>
> Rotation on these backends only reshapes the surface (e.g. 320×480 ↔ 480×320);
> it does not physically rotate, so pointer coordinates need no rotation
> remapping.

## Canvases

Anything you can draw on implements the framebuf API:

- The display itself
- `framebuf` bytearrays
- `graphics.BMP565` bitmap files
- `displaybuf.DisplayBuffer` (see [add-ons](../add-ons.md))

## Timing

pydisplay does not include a task scheduler. Options:

- **`asyncio`** — works on CPython, MicroPython, and PyScript (required there)
- **[multimer](multimer.md)** — cross-platform timers; default `Timer` for sync/threaded loops
- **[multimer](multimer.md#multimeraio-asyncio-timers)** — opt-in asyncio timers for async/PyScript apps

## Vertical scrolling

Many drivers expose **ILI9341-style** vertical scroll: a top fixed band (TFA), a scrollable middle (VSA), and a bottom fixed band (BFA). You define regions with `set_vscroll(tfa, bfa)` or `vscrdef`, then move content with the `vscroll` property (wrapper around `vscsad`).

The [**pydisplay_demo**](../examples/pydisplay_demo.md) guide explains this model with diagrams, covers drawing at `vscroll = 0` during redraw, and shows auto-scroll with `multimer`.

Related examples: [`scroll_touch_test.py`](https://github.com/PyDevices/pydisplay/blob/main/src/examples/scroll_touch_test.py) (touch Up/Down), [`eventsys_encoder_test.py`](https://github.com/PyDevices/pydisplay/blob/main/src/examples/eventsys_encoder_test.py) (encoder).

## Rotation

BusDisplay uses CircuitPython-style rotation degrees (`0`, `90`, `180`, `270`).

Known issues: Unix SDL rotation clears the screen; scrolling while rotated has edge cases on desktop and MCU — see [roadmap](https://github.com/PyDevices/pydisplay#roadmap).

## Next

- [Display backend internals](display-backends.md) — GRAM/present model, 565 API, color conversion per backend
- [Events](events.md)
- [Drawing and fonts](drawing-and-fonts.md)
- [Display drivers (chips)](../hardware/display-drivers.md)

## API reference

[API reference (core)](../reference/) → `displaysys`.
