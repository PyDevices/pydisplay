# CircuitPython

pydisplay works with CircuitPython using Adafruit bus drivers and `framebufferio`.

## Getting started

1. Confirm your display works with Adafruit CircuitPython libraries and DisplayIO first.
2. Copy needed directories from `src/lib/` to your board (`displaysys`, `eventsys`, etc.).
3. Create or adapt a `board_config.py` — use existing configs as templates:

| Config | Use case |
|--------|----------|
| `board_configs/cp/fbdisplay/usb_video` | USB Video (webcam-style output) |
| `board_configs/cp/fbdisplay/qualia_tl040hds20` | Qualia RGB display |
| `board_configs/cp/busdisplay/spi/ili9341_eyespi_qtpy_esp32s3` | EyeSPI ILI9341 on QT Py ESP32-S3 |
| `board_configs/cp/pixeldisplay/neopixel_8x4` | NeoPixel 8×4 grid |
| `board_configs/cp/pixeldisplay/dotstar_12x6` | DotStar 12×6 grid |
| `board_configs/cp/epaperdisplay/magtag` | MagTag E-Ink |

CircuitPython configs live under [`board_configs/cp/`](https://github.com/PyDevices/micropython-hardware/tree/main/board_configs/cp) in micropython-hardware. MicroPython configs stay at the top level of `board_configs/` (not under an `mp/` folder).

CP configs do **not** ship `board_devices.py` or lazy `DEVICES` — CircuitPython’s
native `board` module covers pins/buses. Each CP `board_config.py` provides
`display_drv`, `runtime`, and eager runtime-wired inputs only (`touch`,
`keypad`, `encoder`, `joystick` when present), using the same contract names as
MicroPython.

## BusDisplay on CircuitPython

SPI and I80 displays use `displaysys.busdisplay.BusDisplay` with Adafruit FourWire / ParallelBus drivers.

To prefer pydisplay's BusDisplay over a local shim, patch the graphics driver import:

```python
try:
    from displaysys.busdisplay import BusDisplay
except ImportError:
    from busdisplay import BusDisplay
```

## Framebuffer displays

RGB666 (parallel), USB Video, and HUB75 LED matrices use `displaysys.fbdisplay.FBDisplay` with CircuitPython's `framebufferio.FramebufferDisplay`. No special patching is needed once CircuitPython sees the hardware.

Addressable LED grids (NeoPixel, DotStar) use `displaysys.pixeldisplay.PixelDisplay` with `adafruit_pixel_framebuf`.

## Unix desktop (SDL2)

CircuitPython on Unix can use **`SDLDisplay`** with the native **`usdl2`** module.

Clone as siblings:

```
workspace/
  circuitpython/
  usdl2/
  lv_circuitpython_mod/   # optional LVGL
  pygraphics/             # optional native pygraphics
  pydisplay/              # this repo
```

```bash
# Standalone: patch then make (no cmods required)
cd usdl2 && ./apply_cp_unix_usdl_patches.sh --apply
cd ../circuitpython/ports/unix && make -j VARIANT=coverage
```

With a [cmods](https://github.com/PyDevices/cmods) workspace, `./build_cp.sh` applies usdl2 + pygraphics + LVGL patches then builds:

```bash
./build_cp.sh --port unix --variant coverage
```

Each apply script also runs automatically from `build_cp.sh` for the **unix** port when that sibling exists. If you invoke `make` in `circuitpython/ports/unix` directly, run the patch script(s) yourself first.

Install `libsdl2-dev`, then symlink or copy the built binary (e.g. `ports/unix/build-coverage/micropython`) to `~/bin/circuitpython`.

([cmods](https://github.com/PyDevices/cmods) is an optional convenience workspace for the same sibling layout — not required.)

### Frozen asyncio (required for multimer.AsyncTimer)

CircuitPython unix pydisplay builds must **freeze** Adafruit's `asyncio` and
`adafruit_ticks` libraries into the firmware — do not rely on
`circup install asyncio` at runtime.

```
workspace/
  circuitpython/
  usdl2/
  lv_circuitpython_mod/
  Adafruit_CircuitPython_asyncio/
  Adafruit_CircuitPython_Ticks/
  cp-user-config/user_post_mpconfigport.mk
```

```bash
git clone https://github.com/adafruit/Adafruit_CircuitPython_asyncio.git
git clone https://github.com/adafruit/Adafruit_CircuitPython_Ticks.git
mkdir -p cp-user-config
# Create cp-user-config/user_post_mpconfigport.mk so FROZEN_MPY_DIRS points at
# those clones and MICROPY_PY_ASYNCIO / select / traceback are enabled.
# See [multimer building docs](https://github.com/PyDevices/multimer/blob/main/docs/building.md).

# Standalone patch + make, or cmods ./build_cp.sh which also applies usdl2/pygraphics/LVGL
cd usdl2 && ./apply_cp_unix_usdl_patches.sh --apply && cd ..
cd circuitpython/ports/unix && make -j VARIANT=coverage -I ../../../../cp-user-config
```

When using [cmods](https://github.com/PyDevices/cmods) `build_cp.sh`, it passes `-I cp-user-config/` (workspace sibling) when that
directory exists. See [lv_circuitpython_mod README](https://github.com/PyDevices/lv_circuitpython_mod).

`multimer` supplies Adafruit-compatible `ticks_*` helpers for application code;
frozen asyncio still uses `adafruit_ticks` internally unless the build is customized.

## framebuf

CircuitPython lacks MicroPython-compatible `framebuf`. Use the `framebuf` module
from [PyDevices/pygraphics](https://github.com/PyDevices/pygraphics)
(`lib/pygraphics/framebuf.py`, MIP `pygraphics` / TestPyPI `pygraphics`).

## Installers

CircuitPython `circup` packages are not published yet. Copy files manually from a [full clone](../installation/full-clone.md).

## USB Video note

`board_configs/cp/fbdisplay/usb_video` lets a board appear as a USB webcam streaming the framebuffer. Works on some hosts (e.g. ChromeOS); Windows may not recognize the device.
