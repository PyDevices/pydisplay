# Installation overview

pydisplay supports three install channels. Pick based on whether you need the full repo, source files on device, or precompiled bytecode.

## Comparison

| Channel | Format | Install tool | Includes examples | Includes utils |
|---------|--------|--------------|-------------------|------------------|
| [Full clone](full-clone.md) | Entire repo | `git clone` | Yes | Yes |
| [GitHub MIP](mip-github.md) | Source `.py` | `mip` / `mpremote mip` | Optional (`examples.json`) | Yes (`utils.json`) |
| [micropython-lib MIP](mip-micropython-lib.md) | Precompiled `.mpy` | `mip` with custom index | No | No |

For recommended board setup flows, see [micropython-hardware install workflows](https://pydevices.github.io/micropython-hardware/install-workflows.html).

## What gets installed

**Core libraries** (under `src/lib/`):

- `displaysys` — display drivers (BusDisplay, SDLDisplay, PGDisplay, etc.)
- `eventsys` — input events and Runtime
- `multimer` — cross-platform timers; see [multimer](../concepts/multimer.md)

**Sister packages** (separate repos, installed from the same [micropython-lib MIP index](mip-micropython-lib.md)):

- `pygraphics` — extended drawing helpers ([PyDevices/pygraphics](https://github.com/PyDevices/pygraphics)); see [graphics](../concepts/graphics.md)
- `palettes` — color palettes ([PyDevices/palettes](https://github.com/PyDevices/palettes)); see [palettes guide](../guis/palettes.md)
- `pdwidgets` — widget toolkit ([PyDevices/pdwidgets](https://github.com/PyDevices/pdwidgets)); see [pdwidgets guide](../guis/pywidgets.md)

**Optional packages:**

- `utils` — optional extensions (framebuf shim, console, displaybuf, tft_config, …)
- `examples` — demo scripts
- Bus/touch helpers — see [micropython-hardware packages](https://github.com/PyDevices/micropython-hardware/tree/main/packages)

**Board support** ([micropython-hardware](https://github.com/PyDevices/micropython-hardware)):

- Optional prebuilt `board_config.py` packages per hardware — see [board configs](https://pydevices.github.io/micropython-hardware/board-configs.html) and [install workflows](https://pydevices.github.io/micropython-hardware/install-workflows.html)
- Display and touch drivers under that repo’s `drivers/`
- Desktop SDL (`usdl2`) via the MIP desktop board package or [`pydisplay-desktop`](https://pydevices.github.io/micropython-hardware/pydisplay-desktop.html) on TestPyPI

## PyPI / pip (TestPyPI)

Pure-Python CPython wheels are on [TestPyPI](https://test.pypi.org/) for maintainer testing (not production PyPI). Install with **both** indexes so PyDevices packages and PyPI-only dependencies resolve:

```bash
pip install \
  -i https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple/ \
  displaysys
```

- **`-i` TestPyPI** — primary index for PyDevices packages (`displaysys`, `eventsys`, `pydisplay-desktop`, …; Android APK builds also use TestPyPI `usdl2` wheels).
- **`--extra-index-url` PyPI** — secondary index for dependencies published only on [pypi.org](https://pypi.org) (for example `pygame-ce` when using `PGDisplay`; still `import pygame` at runtime).

Omitting either index causes `pip` to fail: TestPyPI-only packages are not on PyPI, and PyPI-only deps are not on TestPyPI. Full explanation: [Publishing micropython-lib — two-index pip install](../publishing-micropython-lib.md#two-index-pip-install-required).

For day-to-day desktop work without pip, use a [full clone](full-clone.md) or [desktop quick start](../guides/desktop-cpython.md).

## After installing

1. Provide your own `board_config.py` for your hardware, or optionally install a prebuilt board package from micropython-hardware.
2. Follow the quick start for your platform:
   - [ESP32 / MCU](../guides/esp32-board.md)
   - [Desktop CPython](../guides/desktop-cpython.md)
   - [Wokwi](../guides/wokwi.md)

## Troubleshooting

See [Troubleshooting](../troubleshooting.md) for import errors, MIP failures, and display issues.
