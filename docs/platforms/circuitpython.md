# CircuitPython

pydisplay works with CircuitPython using Adafruit bus drivers and `framebufferio`.

## Getting started

1. Confirm your display works with Adafruit CircuitPython libraries and DisplayIO first.
2. Copy needed directories from `src/lib/` to your board (`displaysys`, `eventsys`, etc.).
3. Create or adapt a `board_config.py` — use existing configs as templates:

| Config | Use case |
|--------|----------|
| `board_configs/fbdisplay/cp_usb_video/` | USB Video (webcam-style output) |
| `board_configs/fbdisplay/cp_qualia_tl040hds20/` | Qualia RGB display |
| `board_configs/busdisplay/spi/cp_esp32_pico_eyespi_ili9341/` | SPI ILI9341 |
| `board_configs/pixeldisplay/cp_neopixel_8x8_zigzag/` | NeoPixel 8×8 grid |
| `board_configs/epaperdisplay/cp_magtag/` | MagTag E-Ink |

There is no top-level `board_configs/circuitpython/` directory; per-board configs live alongside MicroPython ones under `board_configs/`.

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

Build from the [cmods](https://github.com/PyDevices/cmods) workspace (sibling trees: `circuitpython/`, `usdl2/`, `lv_circuitpython_mod/`):

```bash
cd ~/github/cmods/usdl2
./apply_cp_unix_usdl_patches.sh --apply   # required before every CP unix compile
cd ~/github/cmods/lv_circuitpython_mod
./build_cp.sh --port unix --variant coverage
```

`build_cp.sh` runs `apply_cp_unix_usdl_patches.sh --apply` automatically for the **unix** port. If you invoke `make` in `circuitpython/ports/unix` directly, run the patch script yourself first.

Install `libsdl2-dev`, then symlink or copy the built binary (e.g. `ports/unix/build-coverage/micropython`) to `~/bin/circuitpython`.

### Frozen asyncio (required for multimer.AsyncTimer)

CircuitPython unix pydisplay builds must **freeze** Adafruit's `asyncio` and
`adafruit_ticks` libraries into the firmware — do not rely on
`circup install asyncio` at runtime.

From the [cmods](https://github.com/PyDevices/cmods) workspace:

```bash
mkdir -p cp-user-config
cp cp-user-config/user_post_mpconfigport.mk.example cp-user-config/user_post_mpconfigport.mk
git clone https://github.com/adafruit/Adafruit_CircuitPython_asyncio.git
git clone https://github.com/adafruit/Adafruit_CircuitPython_Ticks.git
./build_cp.sh --port unix --variant coverage
```

`build_cp.sh` passes `-I cp-user-config/` so `user_post_mpconfigport.mk` sets
`FROZEN_MPY_DIRS` and enables `MICROPY_PY_ASYNCIO` / `select` / `traceback`.
See [multimer building docs](https://github.com/PyDevices/multimer/blob/main/docs/building.md)
and [cmods README](https://github.com/PyDevices/cmods/blob/main/README.md).

`multimer` supplies Adafruit-compatible `ticks_*` helpers for application code;
frozen asyncio still uses `adafruit_ticks` internally unless the build is customized.

## framebuf shim

CircuitPython lacks MicroPython-compatible `framebuf`. Install `add_ons/framebuf.py` or copy it to your `lib/` folder.

## Installers

CircuitPython `circup` packages are not published yet. Copy files manually from a [full clone](../installation/full-clone.md).

## USB Video note

`board_configs/fbdisplay/cp_usb_video/` lets a board appear as a USB webcam streaming the framebuffer. Works on some hosts (e.g. ChromeOS); Windows may not recognize the device. See `assets/screenshots/circuitpython_usb_video_chromebook.gif` in the repo.
