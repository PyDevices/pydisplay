# MicroPython

Platform notes for embedded MCUs and MicroPython on Unix. **Quick start:** [ESP32 board guide](../guides/esp32-board.md).

## Embedded (MCU)

### Requirements

1. A `board_config.py` for your hardware — see [board configs](../hardware/board-configs.md).
2. Core packages (`displaysys`, `eventsys`, …) via [installer.py](../installation/installer.md) or [GitHub MIP](../installation/mip-github.md).
3. `import lib.path` before examples (unless installed into `/lib`).

### Quick start with mpremote

See [ESP32 board guide](../guides/esp32-board.md) for the full install and hello workflow.

Brief version from the repo `src/` directory:

```bash
mpremote mip install "github:PyDevices/pydisplay/board_configs/busdisplay/i80/wt32sc01-plus"
mpremote mount .
```

At the device REPL:

```python
import lib.path
import hello
```

### WSL on Windows

Use [WSL USB Manager](https://gitlab.com/alelec/wsl-usb-gui) to pass USB serial devices into WSL for `mpremote`.

### Bus drivers

SPI displays use `spibus.py`; parallel I80 displays use `i80bus.py`. These install from GitHub only (viper). Board config packages pull them in automatically when needed.

For fastest buses, community C drivers (e.g. [lvgl_micropython](https://github.com/kdschlosser/lvgl_micropython)) can be wired through `BusDisplay`.

## Unix (desktop MicroPython)

Same workflow as [CPython desktop](cpython-desktop.md), but run `micropython -i path.py` instead of `python3`.

Use `board_configs/sdldisplay/` or the default `src/lib/board_config.py` for SDL2-based desktop display.

## usdl2 (native SDL2)

For best SDL2 performance on MicroPython Unix, CircuitPython Unix, and `micropython.exe`, build with the optional native **`usdl2`** module from [PyDevices/usdl2](https://github.com/PyDevices/usdl2). It provides the SDL2 subset used by **`SDLDisplay`** and, when the host selects the SDL timer backend, **`multimer._sdl2`**.

Without **`usdl2`**, `SDLDisplay` falls back to pure-Python ffi/ctypes bindings; timer selection is unchanged (`multimer` still picks `_librt` or threading backends first on each platform).

On **CPython** desktop, the ctypes shim is published on TestPyPI as package **`usdl2`** (install with the [two-index pip pattern](../publishing-micropython-lib.md#two-index-pip-install-required); `displaysys-sdldisplay` pulls it in as a dependency).

## Frozen firmware

The repo-root `manifest.py` lists packages for frozen MicroPython builds and
**freezes `asyncio` on unix and windows ports** (required for `multimer.AsyncTimer`).

Clone this repo as a sibling of `micropython/` (and any native usermods such as
[usdl2](https://github.com/PyDevices/usdl2) / [graphics](https://github.com/PyDevices/graphics)),
then point `FROZEN_MANIFEST` at this file. On **Make** ports,
`USER_C_MODULES` is the workspace parent; build Windows with a variant that
enables `MICROPY_PY_ASYNCIO` and `select` (e.g. `dev`):

```bash
# workspace/
#   micropython/
#   pydisplay/     ← this repo
#   usdl2/         ← optional
#   graphics/      ← optional

cd micropython/ports/unix
make USER_C_MODULES=../../.. FROZEN_MANIFEST=../../../pydisplay/manifest.py

cd micropython/ports/windows
make USER_C_MODULES=../../.. FROZEN_MANIFEST=../../../pydisplay/manifest.py
# use a board/variant that enables asyncio/select as needed
```

([cmods](https://github.com/PyDevices/cmods) `./build_mp.sh` is an optional convenience wrapper for the same sibling layout — not required.)

See [multimer building docs](https://github.com/PyDevices/multimer/blob/main/docs/building.md) and [tools/README.md](https://github.com/PyDevices/pydisplay/blob/main/tools/README.md).
