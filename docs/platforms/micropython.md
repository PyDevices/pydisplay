# MicroPython

Platform notes for embedded MCUs and MicroPython on Unix. **Quick start:** [ESP32 board guide](../guides/esp32-board.md).

## Embedded (MCU)

### Requirements

1. A `board_config.py` for your hardware. You can provide your own, or optionally install a prebuilt board package from pydevices — see [board configs](https://pydevices.github.io/pydevices/board-configs.html) and [install workflows](https://pydevices.github.io/pydevices/install-workflows.html).
2. Core packages (`displaydev`, `eventsys`, …) via [install workflows](https://pydevices.github.io/pydevices/install-workflows.html) or [GitHub MIP](../installation/mip-github.md).
3. If you kept the optional `utils/` package on the device, see [Utils path setup](../utils.md#path-setup) for fallback when environment variables are unavailable or not set as recommended. Skip it if everything is installed flat into `/lib`.

### Quick start with mpremote

See [ESP32 board guide](../guides/esp32-board.md) for the full install and hello workflow.

Brief version from the repo `lib/` directory:

```bash
mpremote mip install "github:PyDevices/pydevices/board_configs/busdisplay/i80/wt32sc01-plus"
mpremote mount .
```

At the device REPL:

```python
import utils.path  # see ../utils.md#path-setup
import hello
```

### WSL on Windows

Use [WSL USB Manager](https://gitlab.com/alelec/wsl-usb-gui) to pass USB serial devices into WSL for `mpremote`.

### Bus drivers

SPI displays use `spibus.py`; parallel I80 displays use `i80bus.py`. These install from GitHub only (viper). Board config packages pull them in automatically when needed.

For fastest buses, community C drivers (e.g. [lvgl_micropython](https://github.com/kdschlosser/lvgl_micropython)) can be wired through `BusDisplay`.

### Background work (`_thread`)

On ESP32, MicroPython worker threads (`_thread` / `mp_thread`) have a very small
stack. Do **not** run network I/O, discovery, or other deep call stacks on a
new thread from a soft timer or input callback — that overflows the stack
(`Stack protection fault` in task `mp_thread`).

Queue the work and run it on the main tick instead: `eventsys.Runtime.on_tick`,
an LVGL `lv.timer`, or a soft `multimer.auto.Timer` pump. Keep UI mutations on that
same main path. Desktop CPython can still use threads; this constraint is for
MCU MicroPython.

## Unix (desktop MicroPython)

Use the same sibling source layout as [CPython desktop](cpython-desktop.md), set
`MICROPYPATH` to pydevices-examples's `src`/`utils` plus the canonical hardware source
trees, and run `micropython examples/<name>.py`.

Install the desktop MIP board package or select a
`pydevices/board_configs/sdldisplay` config for SDL2 output.

## Desktop SDL (`usdl2`)

`SDLDisplay` and the `multimer` `sdl2` timer backend import **`usdl2`** (an SDL2 subset). On desktop hosts, install it with the rest of the desktop board stack:

- **CPython:** [`pydevices-desktop`](https://pydevices.github.io/pydevices/pydevices-desktop.html) from TestPyPI (use the [two-index install](../installation/index.md#pypi-pip-testpypi)), which bundles `usdl2` with the desktop `board_config`
- **MicroPython / CircuitPython Unix (and `micropython.exe`):** the MIP desktop board package from [pydevices](https://github.com/PyDevices/pydevices) (`board_configs/desktop`, which pulls in `drivers/usdl2.py`)

When a native `usdl2` module is already present in the firmware or environment, that build is used; otherwise the pure-Python binding from `pydevices-desktop` / the MIP desktop board provides `import usdl2`. Desktop MicroPython / CircuitPython unix firmware that includes [displayif](https://github.com/PyDevices/displayif) freezes native `usdl2` (it wins over MIP `lib/usdl2.py`). Timer auto-selection is unchanged (`multimer` still prefers `_librt` or threading backends first on each platform).

## Frozen firmware

The product repo's `pydevices/manifest.py` lists the canonical core
packages for frozen MicroPython builds. Upstream port manifests remain
responsible for `asyncio` where `multimer.AsyncTimer` is needed.

Clone this repo as a sibling of `micropython/` (and any native usermods such as
[pygraphics](https://github.com/PyDevices/pygraphics)),
then point `FROZEN_MANIFEST` at this file. On **Make** ports,
`USER_C_MODULES` is the workspace parent; build Windows with a variant that
enables `MICROPY_PY_ASYNCIO` and `select` (e.g. `dev`):

```bash
# workspace/
#   micropython/
#   pydevices/  ← product packages
#   pydevices-examples/             ← examples
#   pygraphics/            ← optional native module

cd micropython/ports/unix
make USER_C_MODULES=../../.. FROZEN_MANIFEST=../../../pydevices/manifest.py

cd micropython/ports/windows
make USER_C_MODULES=../../.. FROZEN_MANIFEST=../../../pydevices/manifest.py
# use a board/variant that enables asyncio/select as needed
```

([cmods](https://github.com/PyDevices/cmods) `./build_mp.sh` is an optional convenience wrapper for the same sibling layout — not required.)

See [multimer](https://pydevices.github.io/pydevices/multimer.html) and the
[example test tools](https://github.com/PyDevices/pydevices-examples/blob/main/tools/README.md).
