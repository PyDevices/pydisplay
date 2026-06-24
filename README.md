<h1 align="center">pydisplay</h1>

<h4 align="center">Cross-platform display and event drivers for MicroPython, CircuitPython, and CPython</h4>

<p align="center">
  <a href="https://pydisplay.readthedocs.io">Documentation</a> •
  <a href="https://PyDevices.github.io/pydisplay/demo/">PyScript demo</a> •
  <a href="https://pydisplay.readthedocs.io/en/latest/guides/wokwi/">Wokwi simulator</a> •
  <a href="screenshots/">Screenshots</a>
</p>

| ![active.py](screenshots/active.gif) | ![tiny_toasters.py](screenshots/tiny_toasters.gif) |
|--------------------------------------|-----------------------------------------------------|
| @peterhinch's active.py              | @russhughes's tiny_toasters.py                      |

## About

pydisplay provides display drivers, unified input events, drawing primitives, fonts, and palettes with one API across **MicroPython**, **CircuitPython**, and **CPython**. Use it standalone for simple UIs or as a foundation for [LVGL](https://github.com/lvgl/lv_micropython), [MicroPython-Touch](https://github.com/peterhinch/micropython-touch), [Nano-GUI](https://github.com/peterhinch/micropython-nano-gui), or custom widget libraries.

Alpha quality — APIs and docs are still evolving. [Contributing](https://pydisplay.readthedocs.io/en/latest/contributing/) and feedback welcome.

**Full documentation:** [pydisplay.readthedocs.io](https://pydisplay.readthedocs.io)

## Quick start

```bash
git clone https://github.com/PyDevices/pydisplay.git
cd pydisplay/src
python3 -i path.py
```

```python
>>> import pydisplay_demo
```

On a MicroPython board, use [installer.py](installer.py) or see [Getting started](https://pydisplay.readthedocs.io/en/latest/getting-started/).

## Install packages (MicroPython)

```python
import mip
mip.install("github:PyDevices/pydisplay/installer.py")
import installer   # runs default install
```

Precompiled packages: [PyDevices micropython-lib MIP index](https://PyDevices.github.io/micropython-lib/mip/PyDevices)

## Key features

- Develop on desktop, deploy to MCU without changing display code
- Touch, mouse, keyboard, keypad, encoder, and joystick as unified events
- `framebuf`-compatible drawing on every platform
- 30+ board configs, 58+ examples, PyScript and Wokwi demos

## Roadmap

- [ ] EPaperDisplay
- [ ] CircuitPython circup packages
- [ ] End-user PyPI wheels
- [ ] More C bus drivers (STM32H7, MIMXRT)

See [GitHub Issues](https://github.com/PyDevices/pydisplay/issues) for details.

## Contributing

Fork, branch, PR — see [Contributing guide](https://pydisplay.readthedocs.io/en/latest/contributing/).

## Thanks

@peterhinch, @russhughes, and the Adafruit CircuitPython team for foundational work in the Python-on-microcontrollers community.
