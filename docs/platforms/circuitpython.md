# CircuitPython

pydevices-examples works with CircuitPython using Adafruit bus drivers and `framebufferio`.

## Getting started

1. Confirm your display works with Adafruit CircuitPython libraries and DisplayIO first.
2. Install the needed unprefixed packages from the PyDevices MIP index
   (`displaydev`, optional `eventsys`, `multimer`, and dependencies).
3. Create or adapt a `board_config.py` — use existing configs as templates:

| Config | Use case |
|--------|----------|
| `board_configs/cp/fbdisplay/usb_video` | USB Video (webcam-style output) |
| `board_configs/cp/fbdisplay/qualia_tl040hds20` | Qualia RGB display |
| `board_configs/cp/busdisplay/spi/ili9341_eyespi_qtpy_esp32s3` | EyeSPI ILI9341 on QT Py ESP32-S3 |
| `board_configs/cp/pixeldisplay/neopixel_8x4` | NeoPixel 8×4 grid |
| `board_configs/cp/pixeldisplay/dotstar_12x6` | DotStar 12×6 grid |

CircuitPython configs live under [`board_configs/cp/`](https://github.com/PyDevices/pydevices/tree/main/board_configs/cp) in pydevices. MicroPython configs stay at the top level of `board_configs/` (not under an `mp/` folder).

CP configs do **not** ship `board_devices.py` or lazy `DEVICES` — CircuitPython’s
native `board` module covers pins/buses. Each CP `board_config.py` provides
`display_drv` and neutral input readers/capabilities when present. The
application instantiates `eventsys` or uses LVGL's `display_driver`.

## BusDisplay on CircuitPython

SPI and I80 displays use `displaydev.busdisplay.BusDisplay` with Adafruit FourWire / ParallelBus drivers.

Chip drivers import pydevices-examples's BusDisplay:

```python
from displaydev.busdisplay import BusDisplay
```

## Framebuffer displays

RGB666 (parallel), USB Video, and HUB75 LED matrices use `displaydev.fbdisplay.FBDisplay` with CircuitPython's `framebufferio.FramebufferDisplay`. No special patching is needed once CircuitPython sees the hardware.

Addressable LED grids (NeoPixel, DotStar) use `displaydev.pixeldisplay.PixelDisplay` with `adafruit_pixel_framebuf`.

## Unix desktop (SDL2)

CircuitPython on Unix can use **`SDLDisplay`**, which imports **`usdl2`**.

When the unix firmware is built with [displayif](https://github.com/PyDevices/displayif)
(`./apply_cp_patches.sh` then the unix coverage build), native `usdl2` is frozen
and wins over MIP `lib/usdl2.py`. Otherwise install the MIP desktop board package
from [pydevices](https://github.com/PyDevices/pydevices)
(`board_configs/desktop`, which includes `drivers/usdl2.py`), or on CPython use
[`pydevices-desktop`](https://pydevices.github.io/pydevices/pydevices-desktop.html)
from TestPyPI. Install `libsdl2-dev` on the host so the SDL library is available.

For a local CircuitPython unix binary, clone as siblings and build the coverage
variant (optional LVGL / pygraphics usermods as needed; include `displayif` for
native `usdl2`):

```
workspace/
  circuitpython/
  displayif/              # native usdl2 (apply_cp_patches.sh)
  lvgl-circuitpython/   # optional LVGL
  pygraphics/             # optional native pygraphics
  pydevices-examples/              # this repo
```

```bash
cd displayif && ./apply_cp_patches.sh --apply --port unix --variant coverage
cd ../circuitpython/ports/unix && make -j VARIANT=coverage
```

Symlink or copy the built binary (e.g. `ports/unix/build-coverage/micropython`)
to `~/bin/circuitpython`.

([cmods](https://github.com/PyDevices/cmods) `./build_cp.sh` is an optional convenience wrapper for the same sibling layout — not required.)

### Frozen asyncio (required for multimer.AsyncTimer)

CircuitPython unix pydevices-examples builds must **freeze** Adafruit's `asyncio` and
`adafruit_ticks` libraries into the firmware — do not rely on
`circup install asyncio` at runtime.

```
workspace/
  circuitpython/
  lvgl-circuitpython/
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
# See [multimer](../concepts/multimer.md).

cd circuitpython/ports/unix && make -j VARIANT=coverage -I ../../../../cp-user-config
```

When using [cmods](https://github.com/PyDevices/cmods) `build_cp.sh`, it passes `-I cp-user-config/` (workspace sibling) when that
directory exists. See [lvgl-circuitpython README](https://github.com/PyDevices/lvgl-circuitpython).

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
