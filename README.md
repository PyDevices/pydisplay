<h1 align="center">PyDisplay</h1>

<h3 align="center">Write your graphics code once. Run it <em>everywhere</em> Python runs.</h3>

<p align="center">
  <b>Cross-platform display, input-event, and timer drivers for MicroPython, CircuitPython, and CPython.</b>
</p>

<p align="center">
  <a href="https://pydisplay.readthedocs.io">Documentation</a> •
  <a href="https://PyDevices.github.io/pydisplay/pyscript/">Browser demo</a> •
  <a href="https://pydisplay.readthedocs.io/en/latest/guides/wokwi/">Wokwi simulator</a> •
   <a href="docs/screenshots/README.md">Screenshot gallery</a>
</p>

| ![paint.py](https://raw.githubusercontent.com/PyDevices/pydisplay/main/docs/screenshots/paint.png) | ![tiny_toasters.py](https://raw.githubusercontent.com/PyDevices/pydisplay/main/docs/screenshots/tiny_toasters.gif) |
|:--:|:--:|
| `paint.py` | @russhughes's `tiny_toasters.py` |

PyDisplay is the portable foundation layer for Python graphics. It gives you **display drivers, unified input events, drawing primitives, fonts, palettes, and cross-platform timers** behind a single API — so the same drawing code runs unchanged on a $4 microcontroller, on your desktop, in a web browser, and even inside a Jupyter Notebook. The published packages are pure-Python: CPython wheels are published on TestPyPI, and MicroPython packages are served through micropython-lib / MIP.

### It really does run everywhere

- **MicroPython** — on microcontrollers, on Unix, on Windows, in the browser via [PyScript](https://pyscript.net/), and in the [Wokwi](https://wokwi.com) online simulator.
- **CircuitPython** — on microcontrollers and on Unix.
- **CPython** — on Unix, on Windows, and in **Jupyter Notebook**.

Develop and debug on your laptop with a mouse, then deploy the *same* code to a touchscreen on an ESP32 — no display rewrite, no input rewrite, no timer rewrite.

### Build real GUIs on top of it

PyDisplay is the graphics, input, and timing backend for a growing family of projects. The sister projects **[lv_micropython_cmod](https://github.com/PyDevices/lv_micropython_cmod)**, **[lv_circuitpython_mod](https://github.com/PyDevices/lv_circuitpython_mod)**, and **[lv_cpython_mod](https://github.com/PyDevices/lv_cpython_mod)** wire PyDisplay into [LVGL](https://lvgl.io/) for MicroPython, CircuitPython, and CPython respectively. That means you can build a polished LVGL application in pure Python — and **you can even develop your LVGL apps interactively in a Jupyter Notebook**, then run the identical code on a microcontroller.

It also drops straight in under [Nano-GUI](https://github.com/peterhinch/micropython-nano-gui), [MicroPython-Touch](https://github.com/peterhinch/micropython-touch), russhughes-style TFT/`st7789py` apps, the sister **[pdwidgets](https://github.com/PyDevices/pdwidgets)** toolkit, or your own widget library.

### Why you'll like it

- **One API, every platform** — `framebuf`-compatible drawing on MicroPython, CircuitPython, and CPython.
- **Unified input** — touch, mouse, keyboard, keypad, rotary encoder, and joystick all arrive as the same PyGame/SDL2-style events.
- **Cross-platform timers** — the `multimer` package gives you `machine.Timer`-style and `asyncio` timers on hosts that have neither.
- **Batteries included** — 30 ready-made board configs, 60+ example scripts, a browser demo, and a Wokwi project.
- **Flexible install** — full git clone, one-line MIP packages, or precompiled `.mpy` bytecode.

> **Alpha quality.** APIs and docs are still evolving fast. [Feedback and contributions](https://pydisplay.readthedocs.io/en/latest/contributing/) are very welcome.

---

## Contents

1. [Introduction](#1-introduction)
   1.1 [What PyDisplay is](#11-what-pydisplay-is)
   1.2 [What PyDisplay is not](#12-what-pydisplay-is-not)
2. [Portability](#2-portability) — the single most important feature: where PyDisplay runs.
3. [Quick start](#3-quick-start)
   3.1 [Try it in the browser](#31-try-it-in-the-browser-no-install) — zero install.
   3.2 [Desktop (CPython)](#32-desktop-cpython)
   3.3 [MicroPython board](#33-micropython-board)
4. [Installation](#4-installation) — clone, MIP, or precompiled packages.
5. [Architecture at a glance](#5-architecture-at-a-glance)
6. [Ecosystem & sister projects](#6-ecosystem--sister-projects) — LVGL in Python, GUIs, Jupyter.
7. [Documentation map](#7-documentation-map) — where everything lives.
8. [Contributing](#8-contributing)
9. [Credits & license](#9-credits--license)

---

## 1. Introduction

### 1.1 What PyDisplay is

PyDisplay is a **foundation layer**, not a GUI toolkit. It provides:

- **`displaysys`** — display backends (`BusDisplay`, `SDLDisplay`, `PGDisplay`, `PSDisplay`, `JNDisplay`, `FBDisplay`) with a unified drawing API.
- **`eventsys`** — a `Runtime` that turns touch, mouse, keyboards, keypads, encoders, and joysticks into uniform PyGame/SDL2-style events.
- **`pygraphics`** — a portable `framebuf`-compatible drawing surface plus shapes, fonts, bitmap loaders, and `Area` helpers.
- **`multimer`** — cross-platform periodic timers (sync, threaded, polled, and `asyncio`) with a `machine.Timer`-style API.

Use it directly for simple UIs, or as the backend for a full widget library.

### 1.2 What PyDisplay is not

- **Not a widget toolkit** — no built-in buttons, sliders, or layout managers (use [LVGL](#6-ecosystem--sister-projects), Nano-GUI, or [pdwidgets](https://github.com/PyDevices/pdwidgets)).
- **Not a task scheduler** — use [`multimer`](https://pydisplay.readthedocs.io/en/latest/concepts/multimer/) or `asyncio` for timing.

See the [Architecture guide](https://pydisplay.readthedocs.io/en/latest/concepts/architecture/) for the full mental model.

## 2. Portability

Portability is PyDisplay's headline feature. The same application code runs on
MicroPython, CircuitPython, and CPython — MCU panels, desktop windows, the
browser (PyScript / Wokwi), and Jupyter. Your code imports `board_config` and
draws; the host selects the display backend.

Full matrix and per-platform notes: **[Portability & platforms](https://pydisplay.readthedocs.io/en/latest/platforms/)**.

## 3. 🚀 Quick start

### 3.1 Try it in the browser (no install)

Open the **[live PyScript demo](https://PyDevices.github.io/pydisplay/pyscript/)** or the **[Wokwi simulator](https://pydisplay.readthedocs.io/en/latest/guides/wokwi/)** — both run real PyDisplay code in your browser with nothing to install.

### 3.2 Desktop (CPython)

```bash
git clone https://github.com/PyDevices/pydisplay.git
cd pydisplay/src
export PYTHONPATH=.:lib:utils
python3 examples/pydisplay_demo.py
```

A display window opens (PyGame or SDL2, whichever is installed). See the [Desktop CPython guide](https://pydisplay.readthedocs.io/en/latest/guides/desktop-cpython/).

### 3.2.1 Path environment forms

Use these environment variable forms when launching from `src/`:

- Unix (MicroPython):

```bash
MICROPYPATH=.:.frozen:lib:utils:~/.micropython/lib:/usr/lib/micropython
```

- Windows (MicroPython):

```powershell
MICROPYPATH=.;.frozen;lib;utils;%USERPROFILE%\.micropython\lib
```

- CPython (Unix and Windows):

```bash
PYTHONPATH=.;lib;utils
```

If environment variables are unavailable or not set as recommended (for example, many MCUs or PyScript),
add this to your startup file so imports are normalized:

- MicroPython: `boot.py` or `main.py`
- CircuitPython: `boot.py` or `code.py`

```python
import utils.path
```

### 3.3 MicroPython board

Use the micropython-hardware install workflows for pip/mip setup and board packages:

- https://pydevices.github.io/micropython-hardware/install-workflows.html

Then pick a [board config](https://pydevices.github.io/micropython-hardware/board-configs.html) for your hardware and follow the [ESP32 board guide](https://pydisplay.readthedocs.io/en/latest/guides/esp32-board/).

You can also create your own `board_config.py` instead of using a prebuilt
board package. If you want prebuilt board packages, use the optional workflow
guide in micropython-hardware:
[install-workflows](https://pydevices.github.io/micropython-hardware/install-workflows.html).

## 4. Installation

| Channel | Format | Best for |
|---------|--------|----------|
| [Full clone](https://pydisplay.readthedocs.io/en/latest/installation/full-clone/) | Entire repo | Development, desktop, contributing |
| [Board install workflows](https://pydisplay.readthedocs.io/en/latest/installation/installer/) | pip / MIP | Recommended setup path for MicroPython boards |
| [GitHub MIP](https://pydisplay.readthedocs.io/en/latest/installation/mip-github/) | Source `.py` | Picking individual packages |
| [micropython-lib MIP](https://pydisplay.readthedocs.io/en/latest/installation/mip-micropython-lib/) | Precompiled `.mpy` | Smallest footprint on device |

Precompiled packages live in the [PyDevices micropython-lib MIP index](https://PyDevices.github.io/micropython-lib/mip/PyDevices). See the [installation overview](https://pydisplay.readthedocs.io/en/latest/installation/) to choose.

## 5. Architecture at a glance

```
   board_config.py          (selects + wires your hardware / platform)
        │
        ├── displaysys  ──►  display_drv   (draw: fill_rect, blit_rect, show, …)
        ├── eventsys    ──►  runtime       (on / poll: touch / mouse / keys / encoder)
        ├── graphics                       (shapes, fonts, framebuf, Area)
        └── multimer                       (periodic + asyncio timers)
        │
        ▼
   your app  ·  LVGL  ·  Nano-GUI  ·  MicroPython-Touch  ·  pdwidgets
```

```python
from board_config import display_drv, runtime

def on_click(event):
    display_drv.fill_rect(0, 0, 10, 10, 0xF800)
    display_drv.show()

runtime.on(runtime.events.MOUSEBUTTONDOWN, on_click)
runtime.run_forever()
```

Full diagram and boot sequence: [Architecture](https://pydisplay.readthedocs.io/en/latest/concepts/architecture/).

## 6. Ecosystem & sister projects

PyDisplay is the graphics, input-event, and timing backend for the wider
PyDevices ecosystem — LVGL bindings for MicroPython, CircuitPython, and CPython
(so you can develop LVGL apps in Jupyter and run the same code on MCU), plus
Nano-GUI, MicroPython-Touch, TFT/`st7789py` ports, and
[pdwidgets](https://github.com/PyDevices/pdwidgets).

Full project list and links: **[Ecosystem & sister projects](https://pydisplay.readthedocs.io/en/latest/ecosystem/)**.

## 7. 📚 Documentation map

Everything lives in one place — the **[documentation site](https://pydisplay.readthedocs.io)**:

| Topic | Start here |
|-------|------------|
| First steps | [Getting started](https://pydisplay.readthedocs.io/en/latest/getting-started/) |
| Where it runs | [Portability & platforms](https://pydisplay.readthedocs.io/en/latest/platforms/) |
| Core concepts | [Architecture](https://pydisplay.readthedocs.io/en/latest/concepts/architecture/), [Displays](https://pydisplay.readthedocs.io/en/latest/concepts/displays/), [Events](https://pydisplay.readthedocs.io/en/latest/concepts/events/), [multimer](https://pydisplay.readthedocs.io/en/latest/concepts/multimer/) |
| Hardware | [Board configs](https://pydevices.github.io/micropython-hardware/board-configs.html) |
| Examples | [Examples catalog](https://pydisplay.readthedocs.io/en/latest/examples/) |
| GUI libraries | [GUI integration](https://pydisplay.readthedocs.io/en/latest/guis/lvgl/) |
| API | [API reference](https://pydisplay.readthedocs.io/en/latest/reference/) |

## 8. 🤝 Contributing

Fork, branch, and open a PR. See the [Contributing guide](https://pydisplay.readthedocs.io/en/latest/contributing/) and the open [GitHub Issues](https://github.com/PyDevices/pydisplay/issues). Roadmap items include EPaper displays, CircuitPython `circup` packages, end-user PyPI wheels, and more C bus drivers.

## 9. Credits & license

PyDisplay is released under the [MIT License](LICENSE). Copyright © 2024 Brad Barnett.

Thanks to **@peterhinch**, **@russhughes**, and the **Adafruit CircuitPython** team for foundational work in the Python-on-microcontrollers community.
