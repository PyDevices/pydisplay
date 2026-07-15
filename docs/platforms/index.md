# Portability & platforms

Portability is PyDisplay's defining feature. Write your display, input, and timing code once against `board_config`, and it runs unchanged across every supported runtime and target below. This page is the single home for the platform matrix; each row links to platform-specific notes.

## Where PyDisplay runs

| Runtime | Microcontrollers | Unix / Linux | Windows | Android | Browser / PWA | Jupyter Notebook |
|---------|:----------------:|:------------:|:-------:|:-------:|:-------------:|:----------------:|
| **[MicroPython](micropython.md)** | ✅ | ✅ | ✅ | — | ✅ [PyScript](pyscript.md) · [PWA](pwa.md) · [Wokwi](../guides/wokwi.md) | — |
| **[CircuitPython](circuitpython.md)** | ✅ | ✅ | — | — | — | — |
| **[CPython](cpython-desktop.md)** | — | ✅ | ✅ | ✅ [Android APK](android.md) | — | ✅ [Jupyter](jupyter.md) |

**Installable browser apps:** the [PyScript gallery](https://pydevices.github.io/pydisplay/pyscript/) ships as a [Progressive Web App](pwa.md) — install it on desktop Chromium, Android Chrome, or iOS home screen. That is a major distribution path, not a demo-only trick. See [where PWAs run](pwa.md#where-pwas-run).

## How portability works

The same import works on every platform:

```python
from board_config import display_drv, runtime
```

What changes is which **display backend** `board_config` selects — automatically on desktop, PyScript, and Jupyter, or explicitly via a per-board config on hardware:

| Backend | Used on | Selected by |
|---------|---------|-------------|
| `BusDisplay` | MicroPython / CircuitPython MCUs (SPI / I80) | [board config](../hardware/board-configs.md) |
| `FBDisplay` | CircuitPython framebuffer displays (RGB, USB video) | board config |
| `SDLDisplay` | CPython, MicroPython Unix, CircuitPython Unix (SDL2); Android APK | auto / `board_configs/sdldisplay/` |
| `PGDisplay` | CPython desktop (PyGame — easy on Windows) | auto / `board_configs/pgdisplay/` |
| `PSDisplay` | [PyScript](pyscript.md) browser canvas and [PWAs](pwa.md) | auto |
| `JNDisplay` | [Jupyter Notebook](jupyter.md) | auto |

Input is just as portable: a mouse on the desktop, a finger on a touchscreen, and a tap in the browser all arrive as the same [events](../concepts/events.md). Timers come from [`multimer`](../concepts/multimer.md), which picks a backend (`machine.Timer`, librt, threads, polling, SDL, or `asyncio`) to suit the host.

See [Displays](../concepts/displays.md) for backend details and [Architecture](../concepts/architecture.md) for how the pieces fit together.

## Platform notes

- [MicroPython](micropython.md) — MCUs, Unix, Windows, bus drivers, frozen firmware.
- [CircuitPython](circuitpython.md) — MCUs and Unix; `framebufferio` and the `framebuf` shim.
- [CPython desktop](cpython-desktop.md) — SDL2 / PyGame setup for Linux, macOS, and Windows.
- [Android](android.md) — CPython APK builds with python-for-android and buildozer.
- [Progressive Web Apps (PWA)](pwa.md) — **where** installable PyScript apps run (desktop, Android Chrome, iOS, TVs).
- [Jupyter Notebook](jupyter.md) — interactive display widget and async execution model.
- [Run the notebook interactively](jupyter-run.md) — JupyterLab / VS Code setup (the RTD notebook page is static).
- [PyScript](pyscript.md) — running in the browser (`PSDisplay`).

## Build GUIs across platforms

Because the backend is portable, anything built on PyDisplay inherits that portability — including the [LVGL sister projects](../ecosystem.md) for MicroPython, CircuitPython, and CPython. You can even prototype an LVGL app in [Jupyter](jupyter.md) and run it unchanged on a microcontroller.
