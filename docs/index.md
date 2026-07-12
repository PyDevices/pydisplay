# PyDisplay

**Write your graphics code once. Run it everywhere Python runs.**

PyDisplay is the portable foundation layer for Python graphics — **display drivers, unified input events, drawing primitives, fonts, palettes, and cross-platform timers** behind a single API. The same drawing code runs unchanged on a microcontroller, on your desktop, in a web browser, and inside a Jupyter Notebook.

PyDisplay is a *foundation*, not a GUI toolkit. Use it directly for simple UIs, or as the backend for [LVGL](guis/lvgl.md), [Nano-GUI](guis/nano-gui.md), [Micro-GUI](guis/micro-gui.md), [MicroPython-Touch](guis/micropython-touch.md), the bundled [PyWidgets](guis/pywidgets.md), or your own widget library.

!!! warning "Alpha quality"
    PyDisplay is under active development. APIs and documentation are still evolving. [Feedback and pull requests](contributing.md) are welcome.

| ![active](https://raw.githubusercontent.com/PyDevices/pydisplay/main/assets/screenshots/active.gif) | ![tiny_toasters](https://raw.githubusercontent.com/PyDevices/pydisplay/main/assets/screenshots/tiny_toasters.gif) |
|:--:|:--:|
| `active.py` | `tiny_toasters.py` |

More in the [screenshot gallery](try/index.md#screenshot-gallery).

## It runs everywhere

Portability is PyDisplay's headline feature:

| Runtime | Microcontrollers | Unix / Linux | Windows | Browser | Jupyter |
|---------|:----------------:|:------------:|:-------:|:-------:|:-------:|
| **MicroPython** | ✅ | ✅ | ✅ | ✅ PyScript · Wokwi | — |
| **CircuitPython** | ✅ | ✅ | — | — | — |
| **CPython** | — | ✅ | ✅ | — | ✅ |

Develop on your laptop with a mouse, then deploy the *same* code to a touchscreen on an ESP32. See **[Portability & platforms](platforms/index.md)** for the full story.

## 🚀 Get started

| I want to… | Start here |
|------------|------------|
| Try it with no install | [Try PyDisplay](try/index.md) |
| Run on an ESP32 / MicroPython board | [ESP32 board guide](guides/esp32-board.md) |
| Develop on desktop (CPython) | [Desktop CPython guide](guides/desktop-cpython.md) |
| See every starting path | [Getting started](getting-started.md) |
| Understand the design | [Architecture](concepts/architecture.md) |

## Key features

- **One API, every platform** — `framebuf`-compatible drawing on MicroPython, CircuitPython, and CPython.
- **Unified input** — touch, mouse, keyboard, keypad, rotary encoder, and joystick all arrive as the same PyGame/SDL2-style [events](concepts/events.md).
- **Cross-platform timers** — [`multimer`](concepts/multimer.md) gives you `machine.Timer`-style and `asyncio` timers even on hosts that have neither.
- **Batteries included** — 30 board configs, 60+ [examples](examples/index.md), a [browser demo](https://PyDevices.github.io/pydisplay/pyscript/), and a [Wokwi](guides/wokwi.md) project.
- **Flexible install** — [full clone](installation/full-clone.md), one-line [MIP packages](installation/mip-github.md), or precompiled `.mpy` bytecode.

## Build GUIs on top of it

PyDisplay is the graphics, input, and timing backend for a growing family of LVGL bindings — [lv_micropython_cmod](https://github.com/PyDevices/lv_micropython_cmod), [lv_circuitpython_mod](https://github.com/PyDevices/lv_circuitpython_mod), and [lv_cpython_mod](https://github.com/PyDevices/lv_cpython_mod). You can build an LVGL app in pure Python, **develop it interactively in a Jupyter Notebook**, and run the identical code on a microcontroller. See [Ecosystem & sister projects](ecosystem.md).

## Quick links

| Resource | URL |
|----------|-----|
| Browser demo | [PyDevices.github.io/pydisplay/pyscript/](https://PyDevices.github.io/pydisplay/pyscript/) |
| Source | [github.com/PyDevices/pydisplay](https://github.com/PyDevices/pydisplay) |
| MIP package index | [PyDevices micropython-lib](https://PyDevices.github.io/micropython-lib/mip/PyDevices) |
| Issues & roadmap | [GitHub Issues](https://github.com/PyDevices/pydisplay/issues) |
