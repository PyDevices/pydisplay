# Displays

pydisplay provides several display driver classes. All expose a drawing surface compatible with MicroPython's `framebuf` API.

See [Architecture](architecture.md) for how drivers connect to `board_config.py`.

## Pick a driver

| Your target | Driver class | Board config example |
|-------------|--------------|----------------------|
| MicroPython MCU (SPI/I80) | `BusDisplay` | `board_configs/busdisplay/spi/...` |
| CPython / MicroPython Unix desktop | `SDLDisplay` | `board_configs/sdldisplay/` |
| Windows CPython (native Win32) | `WinDisplay` | `board_configs/windisplay/` |
| Windows / Chromebook (PyGame easier) | `PGDisplay` | `board_configs/pgdisplay/` |
| CircuitPython RGB / USB video | `FBDisplay` | varies |
| Jupyter notebook | `JNDisplay` | `board_configs/jndisplay/` |
| PyScript browser | `PSDisplay` | `board_configs/psdisplay/` |

Install the matching [board config](https://pydevices.github.io/micropython-hardware/board-configs.html) — it constructs the driver for you.

## Display classes

### BusDisplay

For microcontrollers on **MicroPython and CircuitPython**.

- MicroPython: uses `spibus` / `i80bus` or community C bus drivers ([lvgl_micropython](https://github.com/kdschlosser/lvgl_micropython)).
- CircuitPython: uses Adafruit FourWire / ParallelBus — see [CircuitPython guide](../platforms/circuitpython.md).

### SDLDisplay

SDL2 desktop backend (CPython, MicroPython Unix, CircuitPython Unix). Uses an SDL texture as GRAM. It is the default on MicroPython Unix and available on CPython via `board_configs/sdldisplay/`.

SDL2 bindings for **`SDLDisplay`**: `import usdl2` from [`pydisplay-desktop`](https://pydevices.github.io/micropython-hardware/pydisplay-desktop.html) (TestPyPI) or the MIP desktop board package in [micropython-hardware](https://github.com/PyDevices/micropython-hardware) (`drivers/usdl2.py`). A native `usdl2` module is used when already present in the firmware or environment. See [MicroPython — Desktop SDL](../platforms/micropython.md#desktop-sdl-usdl2).

### WinDisplay

Native Win32 HWND backend for **CPython on Windows** (`uwin32`). Logical RGB565 GRAM, presented with `StretchDIBits`. `displaysys.AutoDisplay` tries it first on `win32` before pygame/SDL. Explicit config: `board_configs/windisplay/`.

### PGDisplay

PyGame desktop backend. `displaysys.AutoDisplay` (used by `board_configs/desktop/`) selects it after `WinDisplay` on Windows, and first on other CPython desktops; if PyGame is not installed it falls back to `SDLDisplay`. Explicit config: `board_configs/pgdisplay/`.

### FBDisplay

Works with CircuitPython `framebufferio.FramebufferDisplay` — dotclock (RGB), USB Video, RGB Matrix.

USB Video lets a board stream the framebuffer as a USB webcam (RP2040; host support varies).

### JNDisplay

Jupyter Notebook output via an interactive `ipywidgets` image. Input (mouse, wheel, keyboard) is captured by `JNDevices` (`ipyevents`) and delivered as events. Config: `board_configs/jndisplay/`.

### PSDisplay

PyScript browser canvas. Input (pointer/touch/pen, wheel, keyboard, gamepad) is captured by `PSDevices` and delivered as events. Config: `board_configs/psdisplay/`. See [PyScript](../guides/pyscript.md).


All display backends feed input into [`eventsys`](events.md) the same way: as a
stream of [`events`](events.md) records drained through a **`HostEventsDevice`**. They
differ only in *how* that stream is produced, which depends on what each
platform exposes:

| Backends | Input source | Wired via |
|----------|--------------|-----------|
| `SDLDisplay`, `PGDisplay`, `WinDisplay` | System-wide OS queue drain (module `get_events`, also on `display_drv.get_events`) | `Runtime(..., host_read=display_drv.get_events)` |
| `JNDisplay`, `PSDisplay` | Per-surface `PSDevices` / `JNDevices`, exposed as `display_drv.get_events` | `Runtime(..., host_read=display_drv.get_events)` |

Either way your handler sees the same `events` objects, so application
code never needs to know which backend is active. Desktop board configs also use
`timer_async=env_bool("PYDISPLAY_TIMER_ASYNC", display_drv.requires_async_timer)`
(`requires_async_timer` is `True` only on PS/JN). `eventsys.Runtime` raises if
`timer_async=False` while any attached display has `requires_async_timer`.

### Desktop (SDL2, PyGame)

SDL2 and PyGame provide a real OS event queue. The driver module drains it and
converts each event to an `events` object:

```python
from displaysys.sdldisplay import SDLDisplay
import eventsys

display_drv = SDLDisplay(...)
runtime = eventsys.Runtime(
    displays=[display_drv],
    host_read=display_drv.get_events,
)
```

Use `poll_event()` only for optional manual single-event checks — not as the
`host_read=` callback (it returns one event, not a list).

Desktop hosts (`SDLDisplay`, `PGDisplay`, `WinDisplay`) set
`display_drv.quit_chord` to **CTRL+Q** (`keys.K_q` + `keys.KMOD_CTRL`).
`HostEventsDevice` matches that chord with `keys.chord_matches` and emits
`events.QUIT`. Window-close still emits `events.QUIT` from SDL/PyGame.
MCU drivers leave `quit_chord` as `None`.

Pointer coordinates use `display_drv.touch_scale` (see `capabilities()` per
backend); `HostEventsDevice` divides mouse events by that scale.

This captures mouse motion/buttons, the wheel, the keyboard, the window-close
(`QUIT`) event, and **joysticks/gamepads** (`JOYAXISMOTION`, `JOYBALLMOTION`,
`JOYHATMOTION`, `JOYBUTTONDOWN`, `JOYBUTTONUP`). Connect controllers before
launching — hot-plugging after startup is not handled.

### Browser / notebook (PyScript, Jupyter)

`PSDevices` (PyScript) and `JNDevices` (Jupyter) capture all available input on
the canvas/widget and turn it into the same `events` objects. The
display owns that drain as `get_events`:

```python
from displaysys.psdisplay import PSDisplay
import eventsys

display_drv = PSDisplay("display_canvas", width, height)
runtime = eventsys.Runtime(
    displays=[display_drv],
    host_read=display_drv.get_events,
    timer_async=display_drv.requires_async_timer,
)
```

Each captures:

- **Pointer** — `MOUSEMOTION` on every move and `MOUSEBUTTONDOWN` /
  `MOUSEBUTTONUP` for any button. On PyScript this uses Pointer Events, so mouse,
  touch, and pen all work (with the `touch` flag set for non-mouse pointers).
- **Wheel** — `MOUSEWHEEL` (also consumed by encoder devices).
- **Keyboard** — `KEYDOWN` / `KEYUP` with SDL-style key codes, names, and
  modifier masks (incl. left/right modifier variants) via `keys` and
  displaysys DOM helpers.
- **Gamepad** (PyScript only) — `JOYAXISMOTION` / `JOYBUTTONDOWN` /
  `JOYBUTTONUP`, polled from the Gamepad API on each `read()`.
- **Quit** — `PSDisplay` / `JNDisplay` set `quit_chord` to browser/TV Back
  (`keys.K_AC_BACK`). `HostEventsDevice` turns that KEYDOWN into `events.QUIT`
  (same as closing an SDL window). Reassign if the host intercepts Back:

```python
import keys

display_drv.quit_chord = (keys.K_c, keys.KMOD_CTRL)  # e.g. CTRL+C on Jupyter
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
- `pygraphics.BMP565` bitmap files
- `displaybuf.DisplayBuffer` (see [utils](../utils.md))

## Timing

pydisplay does not include a task scheduler. Options:

- **`asyncio`** — works on CPython, MicroPython, and PyScript (required there)
- **[multimer](multimer.md)** — cross-platform `Timer` for sync loops; `AsyncTimer` for async/PyScript apps

## Vertical scrolling

Many drivers expose **ILI9341-style** vertical scroll: a top fixed band (TFA), a scrollable middle (VSA), and a bottom fixed band (BFA). You define regions with `set_vscroll(tfa, bfa)` or `vscrdef`, then move content with the `vscroll` property (wrapper around `vscsad`).

The [**pydisplay_demo**](../examples/pydisplay_demo.md) guide explains this model with diagrams, covers drawing at `vscroll = 0` during redraw, and shows auto-scroll with `multimer`.

Related examples: [`scroll_touch_test.py`](https://github.com/PyDevices/pydisplay/blob/main/src/examples/scroll_touch_test.py) (touch Up/Down), [`eventsys_encoder_test.py`](https://github.com/PyDevices/pydisplay/blob/main/src/examples/eventsys_encoder_test.py) (encoder).

## Rotation

BusDisplay uses CircuitPython-style rotation degrees (`0`, `90`, `180`, `270`).

Known issues: Unix SDL rotation clears the screen; scrolling while rotated has edge cases on desktop and MCU — track work on [GitHub Issues](https://github.com/PyDevices/pydisplay/issues).

## Next

- [Display backend internals](display-backends.md) — GRAM/present model, 565 API, color conversion per backend
- [Events](events.md)
- [Drawing and fonts](drawing-and-fonts.md)
- [Display drivers (chips)](https://pydevices.github.io/micropython-hardware/display-drivers.html)

## API reference

[API reference (core)](../reference/) → `displaysys`.
