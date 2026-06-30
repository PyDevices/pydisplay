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

RGB666 (parallel), USB Video, and RGB Matrix devices use `displaysys.fbdisplay.FBDisplay` with CircuitPython's `framebufferio.FramebufferDisplay`. No special patching is needed once CircuitPython sees the hardware.

## Unix desktop (SDL2)

CircuitPython on Unix can use **`SDLDisplay`** with the native **`usdl2`** module — see [MicroPython — usdl2](micropython.md#usdl2-native-sdl2) for build instructions (same `usdl2` repo and patch script).

## framebuf shim

CircuitPython lacks MicroPython-compatible `framebuf`. Install `add_ons/framebuf.py` or copy it to your `lib/` folder.

## Installers

CircuitPython `circup` packages are not published yet. Copy files manually from a [full clone](../installation/full-clone.md).

## USB Video note

`board_configs/fbdisplay/cp_usb_video/` lets a board appear as a USB webcam streaming the framebuffer. Works on some hosts (e.g. ChromeOS); Windows may not recognize the device. See `assets/screenshots/circuitpython_usb_video_chromebook.gif` in the repo.
