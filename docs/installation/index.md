# Installation overview

pydevices-examples supports three install channels. Pick based on whether you need the full repo, source files on device, or precompiled bytecode.

## Comparison

| Channel | Format | Install tool | Includes examples | Includes utils |
|---------|--------|--------------|-------------------|------------------|
| [Full clone](full-clone.md) | Entire repo | `git clone` | Yes | Yes |
| [GitHub MIP](mip-github.md) | Source `.py` | `mip` / `mpremote mip` | Optional (`examples.json`) | Yes (`utils.json`) |
| [micropython-lib MIP](mip-micropython-lib.md) | Precompiled `.mpy` | `mip` with custom index | No | No |

For recommended board setup flows, see [pydevices install workflows](https://pydevices.github.io/pydevices/install-workflows.html).

## What gets installed

**Product libraries** (canonical source in [pydevices](https://github.com/PyDevices/pydevices), published through MIP and TestPyPI):

- `eventsys` — optional application event traffic controller
- `audiodev` — portable PCM audio interfaces
- `displaydev` — display drivers (BusDisplay, SDLDisplay, PGDisplay, etc.) from [pydevices](https://github.com/PyDevices/pydevices)
- `multimer` — cross-platform timers; see [multimer](../concepts/multimer.md) (pydevices)
- `events` / `keys` — event types and key codes (pydevices)

**Sister packages** (separate repos, installed from the same [micropython-lib MIP index](mip-micropython-lib.md)):

- `pygraphics` — extended drawing helpers ([PyDevices/pygraphics](https://github.com/PyDevices/pygraphics)); see [graphics](../concepts/graphics.md)
- `palettes` — color palettes ([PyDevices/palettes](https://github.com/PyDevices/palettes)); see [palettes guide](../guis/palettes.md)
- `pdwidgets` — widget toolkit ([PyDevices/pdwidgets](https://github.com/PyDevices/pdwidgets)); see [pdwidgets guide](../guis/pywidgets.md)

**Optional packages:**

- `utils` — optional extensions (framebuf shim, console, displaybuf, tft_config, …); `byteswap` / `mip` / `viper_tools` / `keypins` / `wifi` / `frame_recorder` come from [pydevices `utils/`](https://github.com/PyDevices/pydevices/tree/main/utils)
- `examples` — demo scripts
- Bus/touch helpers — see [pydevices packages](https://github.com/PyDevices/pydevices/tree/main/packages)

**Board support** ([pydevices](https://github.com/PyDevices/pydevices)):

- Optional prebuilt `board_config.py` packages per hardware — see [board configs](https://pydevices.github.io/pydevices/board-configs.html) and [install workflows](https://pydevices.github.io/pydevices/install-workflows.html)
- Display and touch drivers under that repo’s `drivers/`
- Desktop SDL (`usdl2`) via the MIP desktop board package or [`pydevices-desktop`](https://pydevices.github.io/pydevices/pydevices-desktop.html) on TestPyPI

## PyPI / pip (TestPyPI)

Pure-Python CPython wheels are on [TestPyPI](https://test.pypi.org/) for maintainer testing (not production PyPI). Install with **both** indexes so PyDevices packages and PyPI-only dependencies resolve:

```bash
pip install \
  -i https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple/ \
  pydevices-desktop pydevices-eventsys
```

- **`-i` TestPyPI** — primary index for prefixed PyDevices distributions (`pydevices-displaydev`, `pydevices-eventsys`, `pydevices-desktop`, …).
- **`--extra-index-url` PyPI** — secondary index for dependencies published only on [pypi.org](https://pypi.org) (for example `pygame-ce` when using `PGDisplay`; still `import pygame` at runtime).

Omitting either index causes `pip` to fail: TestPyPI-only packages are not on PyPI, and PyPI-only dependencies are not on TestPyPI. See [product package publishing](../publishing-micropython-lib.md).

For day-to-day desktop work without pip, use a [full clone](full-clone.md) or [desktop quick start](../guides/desktop-cpython.md).

## After installing

1. Provide your own `board_config.py` for your hardware, or optionally install a prebuilt board package from pydevices.
2. Follow the quick start for your platform:
   - [ESP32 / MCU](../guides/esp32-board.md)
   - [Desktop CPython](../guides/desktop-cpython.md)
   - [Wokwi](../guides/wokwi.md)

## Troubleshooting

See [Troubleshooting](../troubleshooting.md) for import errors, MIP failures, and display issues.
