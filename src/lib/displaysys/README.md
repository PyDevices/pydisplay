# displaysys

Cross-platform display drivers for MicroPython, CircuitPython, and CPython — `BusDisplay`, `SDLDisplay`, `PGDisplay`, `PSDisplay`, `JNDisplay`, `FBDisplay`, and more behind one drawing API.

## Install

### CPython (TestPyPI)

This package is published as a pure-Python wheel to TestPyPI.

```bash
pip install \
  -i https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple/ \
  displaysys
```

Why both indexes: [two-index pip install](https://pydisplay.readthedocs.io/en/latest/publishing-micropython-lib/#two-index-pip-install-required).

For desktop SDL, also install native `usdl2` (or pure-Python `usdl2-py`) with the same two-index pattern. For PyGame, install `pygame-ce` from PyPI (`import pygame`).

### MicroPython (MIP)

```python
import mip
mip.install("displaysys", index="https://PyDevices.github.io/micropython-lib/mip/PyDevices")
```

## Quick start

Apps normally import a `board_config` (from micropython-hardware / `pydisplay-desktop`) that wires the display and `eventsys.Runtime`:

```python
from board_config import display_drv, runtime

display_drv.fill(0)
display_drv.fill_rect(10, 10, 40, 40, 0xF800)
display_drv.show()
```

Host auto-selection lives in displaysys:

```python
from displaysys import AutoDisplay
import eventsys

display_drv = AutoDisplay(width=320, height=480, scale=2.0)
runtime = eventsys.Runtime(
    displays=[display_drv],
    host_read=display_drv.get_events,
    timer_async=display_drv.requires_async_timer,
)
```

`AutoDisplay` picks `PSDisplay` (PyScript), `JNDisplay` (Jupyter), or
`PGDisplay`→`SDLDisplay` (desktop). Install a board package for MCU pins, or
use the desktop bundle from micropython-hardware
([install workflows](https://pydevices.github.io/micropython-hardware/install-workflows.html)).

## What you get

- Unified `framebuf`-style drawing surface (`fill`, `fill_rect`, `blit_rect`, `show`, …)
- MCU (`BusDisplay`, `FBDisplay`, e-paper) and host backends (SDL, PyGame, Jupyter, PyScript)
- `AutoDisplay` / `host_kind` for desktop-like host selection (board_config remains the app import surface)

Desktop input backends use [eventsys](https://test.pypi.org/project/eventsys/) at runtime; install it separately when you need `Runtime` / host events.

## Links

- [Documentation — Displays](https://pydisplay.readthedocs.io/en/latest/concepts/displays/)
- [Source](https://github.com/PyDevices/pydisplay)
- [Issues](https://github.com/PyDevices/pydisplay/issues)
- Related: [eventsys](https://test.pypi.org/project/eventsys/), [multimer](https://test.pypi.org/project/multimer/), [pygraphics](https://test.pypi.org/project/pygraphics/), [usdl2](https://test.pypi.org/project/usdl2/), [usdl2-py](https://test.pypi.org/project/usdl2-py/)

## License

MIT — see [LICENSE](https://github.com/PyDevices/pydisplay/LICENSE).
