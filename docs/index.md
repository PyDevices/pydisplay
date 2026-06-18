# pydisplay

Cross-platform display and event drivers for MicroPython, CircuitPython, and CPython.

pydisplay is a foundation for GUI libraries — not a GUI itself. It provides display drivers, touch and input events, drawing primitives, fonts, and palettes with a consistent API across platforms. Use it directly for simple apps, or pair it with [LVGL](https://github.com/lvgl/lv_micropython), [MicroPython-Touch](https://github.com/peterhinch/micropython-touch), [Nano-GUI](https://github.com/peterhinch/micropython-nano-gui), or your own framework.

!!! warning "Alpha quality"
    pydisplay is under active development. APIs and documentation are still catching up with the code. Feedback and pull requests are welcome.

## Choose your path

| I want to… | Start here |
|------------|------------|
| Try in the browser (no install) | [Try pydisplay → PyScript](try/index.md) |
| Try in Wokwi simulator | [Try pydisplay → Wokwi](try/index.md#wokwi-simulator) |
| Run on ESP32 / MicroPython board | [ESP32 quick start](guides/esp32-board.md) |
| Develop on desktop (CPython) | [Desktop quick start](guides/desktop-cpython.md) |
| Browse all options | [Getting started](getting-started.md) |

## Key features

- **One API, many platforms** — develop on desktop CPython, deploy to MicroPython on ESP32-S3, or run in CircuitPython without rewriting display code.
- **Unified input** — touchscreens, mice, keypads, keyboards, rotary encoders, and joysticks produce consistent events modeled on PyGame/SDL2.
- **Drawing** — MicroPython `framebuf` API everywhere; optional `graphics` module with extra helpers such as rounded rectangles.
- **Examples** — dozens of scripts in `src/examples/`, including ports from [st7789py_mpy](https://github.com/russhughes/st7789py_mpy).
- **Flexible install** — full git clone, GitHub MIP packages, or precompiled packages from the [PyDevices micropython-lib index](https://PyDevices.github.io/micropython-lib/mip/PyDevices).

## Quick links

| Resource | URL |
|----------|-----|
| Documentation | [pydisplay.readthedocs.io](https://pydisplay.readthedocs.io) |
| PyScript browser demo | [PyDevices.github.io/pydisplay/demo/](https://PyDevices.github.io/pydisplay/demo/) |
| Source | [github.com/PyDevices/pydisplay](https://github.com/PyDevices/pydisplay) |
| MIP package index | [PyDevices micropython-lib](https://PyDevices.github.io/micropython-lib/mip/PyDevices) |

## Screenshots

| active.py | tiny_toasters.py |
|-----------|------------------|
| ![active](https://raw.githubusercontent.com/PyDevices/pydisplay/main/screenshots/active.gif) | ![tiny_toasters](https://raw.githubusercontent.com/PyDevices/pydisplay/main/screenshots/tiny_toasters.gif) |

More: [Try pydisplay gallery](try/index.md#screenshot-gallery).

## What pydisplay is not

- Not a widget toolkit — no built-in buttons, sliders, or layout managers.
- Not a task scheduler — use [multimer](concepts/displays.md#timing) or `asyncio` for timing.
- Not a GUI library — pair with LVGL, MicroPython-Touch, PyWidgets (`add_ons/pdwidgets`), or roll your own.

See [Architecture](concepts/architecture.md) for the full mental model.
