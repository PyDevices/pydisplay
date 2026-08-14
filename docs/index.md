# PyDevices examples and integrations

**See the portable PyDevices driver stack in action.**

This site documents the examples, third-party GUI integrations, and PyScript
gallery in the `pydevices-examples` repository. Reusable package source, hardware drivers,
board configs, and publishing live in
[`pydevices`](https://github.com/PyDevices/pydevices).

The same examples can run on MicroPython, CircuitPython, and CPython across
microcontrollers, desktop hosts, browsers, Android, Wokwi, and Jupyter notebooks.

!!! warning "Alpha quality"
    The organization is being prepared for its first external users, so names
    and APIs may still evolve.

| ![paint](https://raw.githubusercontent.com/PyDevices/pydevices-examples/main/docs/screenshots/paint.png) | ![tiny_toasters](https://raw.githubusercontent.com/PyDevices/pydevices-examples/main/docs/screenshots/tiny_toasters.gif) |
|:--:|:--:|
| `paint.py` | `tiny_toasters.py` |

More examples are in the [screenshot gallery](screenshots/README.md).

## Start here

| I want to… | Start here |
|---|---|
| Run an example without installing anything | [Live PyScript gallery](https://PyDevices.github.io/pydevices-examples/pyscript/) |
| Make my own browser-installable app | [PyScript PWA guide](guides/pyscript-pwa.md) |
| Install product packages or configure a board | [pydevices workflows](https://pydevices.github.io/pydevices/install-workflows.html) |
| Run the examples on desktop | [Desktop CPython guide](guides/desktop-cpython.md) |
| Run on an ESP32 / MicroPython board | [ESP32 board guide](guides/esp32-board.md) |
| Browse every example | [Example catalog](examples/index.md) |
| Understand the application wiring | [Architecture](https://pydevices.github.io/pydevices/architecture.html) |

## Product and showcase

`pydevices` is the product repository. It owns `displaydev`,
`audiodev`, `events`, `keys`, `multimer`, optional `eventsys`, board configs,
board peripherals, hardware drivers, and their TestPyPI/MIP release automation.

`pydevices-examples` is the showcase. It owns examples, application utilities, integration
guides, the PyScript gallery, and the reusable PWA shell.

Board configs export hardware capabilities but do not instantiate an application
runtime. Non-LVGL examples explicitly import `runtime` from `app_runtime`; LVGL
examples import `runtime` from `display_driver`, whose implementation is shared
by the LVGL binding repositories and is independent of `eventsys`.

## Package naming

TestPyPI distribution names use `pydevices-` (for example,
`pydevices-displaydev`). Python imports and MIP package names stay unprefixed
(`import displaydev`, `mip.install("displaydev", ...)`). See the
[installation guide](installation/index.md) for the complete mapping.

## Quick links

| Resource | Link |
|---|---|
| Browser gallery | [PyDevices.github.io/pydevices-examples/pyscript](https://PyDevices.github.io/pydevices-examples/pyscript/) |
| Product source | [PyDevices/pydevices](https://github.com/PyDevices/pydevices) |
| Example source | [PyDevices/pydevices-examples](https://github.com/PyDevices/pydevices-examples) |
| MIP index | [PyDevices micropython-lib](https://PyDevices.github.io/mip) |
