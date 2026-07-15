# Installation overview

pydisplay supports three install channels. Pick based on whether you need the full repo, source files on device, or precompiled bytecode.

## Comparison

| Channel | Format | Install tool | Includes examples | Includes add_ons |
|---------|--------|--------------|-------------------|------------------|
| [Full clone](full-clone.md) | Entire repo | `git clone` | Yes | Yes |
| [GitHub MIP](mip-github.md) | Source `.py` | `mip` / `mpremote mip` | Optional (`examples.json`) | Yes (`add_ons.json`) |
| [micropython-lib MIP](mip-micropython-lib.md) | Precompiled `.mpy` | `mip` with custom index | No | No |

The [installer.py](installer.md) script combines GitHub and micropython-lib installs in one call — recommended for MicroPython boards.

## What gets installed

**Core libraries** (under `src/lib/`):

- `displaysys` — display drivers (BusDisplay, SDLDisplay, PGDisplay, etc.)
- `eventsys` — input events and Runtime
- `graphics` — extended drawing helpers
- `multimer` — cross-platform timers; see [multimer](../concepts/multimer.md)

**Optional packages:**

- `add_ons` — optional extensions (framebuf shim, console, displaybuf, tft_config, …); [`palettes`](guis/palettes.md) and [`pdwidgets`](guis/pywidgets.md) are separate packages
- `examples` — demo scripts
- `spibus` / `i80bus` — MicroPython bus drivers (viper; GitHub only)

**Board support:**

- `board_config.py` per hardware — see [board configs](../hardware/board-configs.md)
- Display and touch drivers from `drivers/`

## PyPI / pip (TestPyPI)

CPython wheels are on [TestPyPI](https://test.pypi.org/) for maintainer testing (not production PyPI). Install with **both** indexes so PyDevices packages and PyPI-only dependencies resolve:

```bash
pip install \
  -i https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple/ \
  displaysys displaysys-pgdisplay
```

- **`-i` TestPyPI** — primary index for PyDevices packages (`displaysys`, `eventsys`, `usdl2`, …).
- **`--extra-index-url` PyPI** — secondary index for dependencies published only on [pypi.org](https://pypi.org) (for example `pygame-ce` when installing `displaysys-pgdisplay`; still `import pygame` at runtime).

Omitting either index causes `pip` to fail: TestPyPI-only packages are not on PyPI, and PyPI-only deps are not on TestPyPI. Full explanation: [Publishing micropython-lib — two-index pip install](../publishing-micropython-lib.md#two-index-pip-install-required).

For day-to-day desktop work without pip, use a [full clone](full-clone.md) or [desktop quick start](../guides/desktop-cpython.md).

## After installing

1. Provide or install a `board_config.py` matching your hardware.
2. Follow the quick start for your platform:
   - [ESP32 / MCU](../guides/esp32-board.md)
   - [Desktop CPython](../guides/desktop-cpython.md)
   - [Wokwi](../guides/wokwi.md)

## Troubleshooting

See [Troubleshooting](../troubleshooting.md) for import errors, MIP failures, and display issues.
