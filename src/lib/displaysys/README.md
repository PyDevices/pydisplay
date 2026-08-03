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

For desktop SDL, also install native `usdl2` (or pure-Python `usdl2-py`) with the same two-index pattern. For PyGame, install `pygame-ce` from PyPI (`import pygame`).

### MicroPython (MIP)

```python
import mip
mip.install("displaysys", index="https://PyDevices.github.io/micropython-lib/mip/PyDevices")
```

## Quick start

```python
from board_config import display_drv

display_drv.fill(0)
display_drv.fill_rect(10, 10, 40, 40, 0xF800)
display_drv.show()
```

`board_config` is included in this wheel and selects a desktop backend when run on CPython. On MCU boards, install a matching board config from the [pydisplay](https://github.com/PyDevices/pydisplay) repo.

## What you get

- Unified `framebuf`-style drawing surface (`fill`, `fill_rect`, `blit_rect`, `show`, …)
- MCU (`BusDisplay`, `FBDisplay`, e-paper) and host backends (SDL, PyGame, Jupyter, PyScript)
- Default `board_config.py` for desktop quick starts

Desktop input backends use [eventsys](https://test.pypi.org/project/eventsys/) at runtime; install it separately when you need `Runtime` / host events.

## Links

- [Documentation — Displays](https://pydisplay.readthedocs.io/en/latest/concepts/displays/)
- [Source](https://github.com/PyDevices/pydisplay)
- [Issues](https://github.com/PyDevices/pydisplay/issues)
- Related: [eventsys](https://test.pypi.org/project/eventsys/), [multimer](https://test.pypi.org/project/multimer/), [pygraphics](https://test.pypi.org/project/pygraphics/), [usdl2](https://test.pypi.org/project/usdl2/), [usdl2-py](https://test.pypi.org/project/usdl2-py/)

## License

MIT — see [LICENSE](https://github.com/PyDevices/pydisplay/blob/main/LICENSE).
