# Ecosystem & sister projects

PyDevices is the graphics, input-event, and timing backend for the wider PyDevices ecosystem. Anything built on top of it inherits PyDevices's [portability](platforms/index.md) across MicroPython, CircuitPython, and CPython.

## LVGL sister projects

Three sister projects wire the PyDevices portable stack into [LVGL](https://lvgl.io/) — the popular C graphics library — so you can build LVGL applications in pure Python. They use `displaydev`, neutral board input, and `multimer` on each runtime, while pydevices-examples hosts the examples:

| Project | Runtime | Role |
|---------|---------|------|
| [lvgl-micropython](https://github.com/PyDevices/lvgl-micropython) | MicroPython | LVGL bindings; PyDevices drives display + input. |
| [lvgl-circuitpython](https://github.com/PyDevices/lvgl-circuitpython) | CircuitPython | LVGL bindings backed by PyDevices. |
| [lvgl-python](https://github.com/PyDevices/lvgl-python) | CPython | LVGL bindings backed by PyDevices. |

Because all three share PyDevices as the backend, the *same* LVGL Python code runs on a microcontroller, on the desktop, and — see below — in a notebook.

### Develop LVGL apps in Jupyter Notebook

With the CPython backend you can build and iterate on an LVGL UI **interactively in a Jupyter Notebook**: run a cell to create widgets, run another to modify them, and watch the display update live in an interactive widget. When you are happy, run the identical code on hardware.

See the [LVGL guide](guis/lvgl.md) for wiring details and the [Jupyter platform notes](platforms/jupyter.md) for the async execution model.

## GUI library integration

PyDevices also drops in under other GUI stacks:

| Library | Notes |
|---------|-------|
| [LVGL](guis/lvgl.md) | Full-featured C toolkit via the sister projects above. |
| [Nano-GUI](guis/nano-gui.md) | @peterhinch's lightweight `FrameBuffer` GUI (display-only). |
| [Micro-GUI](guis/micro-gui.md) | @peterhinch's button / encoder GUI. |
| [MicroPython-Touch](guis/micropython-touch.md) | @peterhinch's touch GUI. |
| [TFT / st7789py ports](guis/tft-gui.md) | russhughes-style font and bitmap rendering. |
| [pdwidgets](https://github.com/PyDevices/pdwidgets) | Cross-platform widget toolkit for PyDevices. |
| [palettes](https://github.com/PyDevices/palettes) | Color palettes (`wheel`, `cube`, `material_design`). |

## Related PyDevices repositories

- [pydevices-examples](https://github.com/PyDevices/pydevices-examples) — this project.
- [palettes](https://github.com/PyDevices/palettes) — color palette toolkit.
- [pdwidgets](https://github.com/PyDevices/pdwidgets) — widget toolkit for PyDevices.
- [mip](https://github.com/PyDevices/mip) — precompiled MIP packages ([index](https://PyDevices.github.io/mip)).
- [displayif](https://github.com/PyDevices/displayif) — native MicroPython display interface modules for PyDevices.
