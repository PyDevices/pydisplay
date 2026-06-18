# pydisplay

Cross-platform display and event drivers for MicroPython, CircuitPython, and CPython.

pydisplay is a foundation for GUI libraries — not a GUI itself. It provides display drivers, touch and input events, drawing primitives, fonts, and palettes with a consistent API across platforms. Use it directly for simple apps, or pair it with [LVGL](https://github.com/lvgl/lv_micropython), [MicroPython-Touch](https://github.com/peterhinch/micropython-touch), [Nano-GUI](https://github.com/peterhinch/micropython-nano-gui), or your own framework.

!!! warning "Alpha quality"
    pydisplay is under active development. APIs and documentation are still catching up with the code. Feedback and pull requests are welcome.

## Key features

- **One API, many platforms** — develop on desktop CPython, deploy to MicroPython on ESP32-S3, or run in CircuitPython without rewriting display code.
- **Unified input** — touchscreens, mice, keypads, keyboards, rotary encoders, and joysticks produce consistent events modeled on PyGame/SDL2.
- **Drawing** — MicroPython `framebuf` API everywhere; optional `graphics` module with extra helpers such as rounded rectangles.
- **Examples** — dozens of scripts in `src/examples/`, including ports from [st7789py_mpy](https://github.com/russhughes/st7789py_mpy).
- **Flexible install** — full git clone, GitHub MIP packages, or precompiled packages from the [PyDevices micropython-lib index](https://PyDevices.github.io/micropython-lib/mip/PyDevices).

## Quick links

| Resource | URL |
|----------|-----|
| Getting started | [getting-started.md](getting-started.md) |
| PyScript browser demo | [PyDevices.github.io/pydisplay/demo/](https://PyDevices.github.io/pydisplay/demo/) |
| Wokwi ESP32-S3 example | [wokwi.com/projects/415770470006384641](https://wokwi.com/projects/415770470006384641) |
| Source | [github.com/PyDevices/pydisplay](https://github.com/PyDevices/pydisplay) |
| MIP package index | [PyDevices micropython-lib](https://PyDevices.github.io/micropython-lib/mip/PyDevices) |

## Screenshots

| active.py | tiny_toasters.py |
|-----------|------------------|
| ![active](https://raw.githubusercontent.com/PyDevices/pydisplay/main/screenshots/active.gif) | ![tiny_toasters](https://raw.githubusercontent.com/PyDevices/pydisplay/main/screenshots/tiny_toasters.gif) |

More screenshots are in the [live demos](examples/live-demos.md) page.

## What pydisplay is not

- Not a widget toolkit — no built-in buttons, sliders, or layout managers.
- Not a task scheduler — use [multimer](concepts/displays.md#timing) or `asyncio` for timing.
- Not a GUI library — pair with LVGL, MicroPython-Touch, PyWidgets (`add_ons/pdwidgets`), or roll your own.
