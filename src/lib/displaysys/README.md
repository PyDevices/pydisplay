# displaysys

Cross-platform display drivers for MicroPython, CircuitPython, and CPython — `BusDisplay`, `SDLDisplay`, `PGDisplay`, `WinDisplay`, `PSDisplay`, `JNDisplay`, `FBDisplay`, and more behind one drawing API.

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

For desktop SDL, also install [`pydisplay-desktop`](https://test.pypi.org/project/pydisplay-desktop/) with the same two-index pattern (bundles `usdl2` and the desktop `board_config`). For PyGame, install `pygame-ce` from PyPI (`import pygame`).

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
`WinDisplay`→`PGDisplay`→`SDLDisplay` (desktop; Win32 first on Windows
CPython). Explicit boards import a backend directly. Install a board package
for MCU pins, or
use the desktop bundle from micropython-hardware
([install workflows](https://pydevices.github.io/micropython-hardware/install-workflows.html)).

## What you get

- Unified `framebuf`-style drawing surface (`fill`, `fill_rect`, `blit_rect`, `show`, …)
- MCU (`BusDisplay`, `FBDisplay`) and host backends (SDL, PyGame, Jupyter, PyScript)
- `AutoDisplay` / `host_kind` for desktop-like host selection (board_config remains the app import surface)

Host backends use [pydisplay-events](https://test.pypi.org/project/pydisplay-events/) and [pydisplay-keys](https://test.pypi.org/project/pydisplay-keys/) for event records and key codes (`import events` / `import keys`). Install [eventsys](https://test.pypi.org/project/eventsys/) separately when you need `Runtime` / host event polling.

## Links

- [Documentation — Displays](https://pydisplay.readthedocs.io/en/latest/concepts/displays/)
- [Source](https://github.com/PyDevices/pydisplay)
- [Issues](https://github.com/PyDevices/pydisplay/issues)
- Related: [pydisplay-events](https://test.pypi.org/project/pydisplay-events/), [pydisplay-keys](https://test.pypi.org/project/pydisplay-keys/), [eventsys](https://test.pypi.org/project/eventsys/), [multimer](https://test.pypi.org/project/multimer/), [pygraphics](https://test.pypi.org/project/pygraphics/), [pydisplay-desktop](https://test.pypi.org/project/pydisplay-desktop/)

## License

MIT — see [LICENSE](https://github.com/PyDevices/pydisplay/LICENSE).
