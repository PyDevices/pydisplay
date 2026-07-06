# Display interfaces

Maps hardware interface types to pydisplay `displaysys` backends and pydevices/cmods work for MicroPython parity.

## Interface matrix

| Interface | Industry term | CircuitPython module | displaysys backend | MicroPython bus | pydevices status |
|-----------|---------------|----------------------|-------------------|-----------------|------------------|
| SPI + MIPI DCS | SPI TFT | `fourwire.FourWire` + chip driver | **BusDisplay** | `SPIBus` | Done |
| 8080 8-bit parallel | I80 parallel | `paralleldisplaybus.ParallelBus` | **BusDisplay** | `I80Bus` | Bit-bang done; PIO WIP |
| I2C DCS | I2C OLED | `i2cdisplaybus.I2CDisplayBus` | **BusDisplay** | `I2CBus` (planned) | Not started |
| RGB parallel timed | RGB565 / **RGB666** | `dotclockframebuffer` | **FBDisplay** | `rgbframebuffer` | External / cmod |
| HUB75 LED matrix | HUB75 | `rgbmatrix.RGBMatrix` | **FBDisplay** | `rgbmatrix` | Not started |
| WS2812 / DotStar grid | Addressable LED matrix | `adafruit_pixel_framebuf` | **PixelDisplay** | neopixel + mapper | Not started |
| SPI E-ink | E-paper | `epaperdisplay.EPaperDisplay` chip drivers | **EPaperDisplay** (stub) | SPI + chip driver | Stub only |
| USB UVC gadget | USB Video | `usb_video` | **FBDisplay** | N/A | CP only |
| MIPI DSI | MIPI DSI | SoC firmware | TBD | DSI host | Not started |

**Note:** MIPI **DCS** (Display Command Set) over SPI/I80 is not MIPI **DSI** (the high-speed serial panel interface).

## Board config directories

| Backend | Path | Example |
|---------|------|---------|
| BusDisplay | `board_configs/busdisplay/{spi,i80,i2c}/` | `cp_pyportal`, `ili9341_eyespi_qtpy_esp32s3` |
| FBDisplay | `board_configs/fbdisplay/` | `cp_qualia_tl040hds20`, `cp_matrixportal_s3_64x64` |
| PixelDisplay | `board_configs/pixeldisplay/` | `cp_neopixel_8x8_zigzag` |
| EPaperDisplay | `board_configs/epaperdisplay/` | `cp_magtag` |

## Touch

Touch controllers live in `drivers/touch/`. CircuitPython shims are under `drivers/touch/circuitpython/`. Every applicable `board_config.py` should wire:

- `touch_read_func` — returns `(x, y)` or `None`
- `touch_rotation_table` — maps display rotation to touch coordinates
- `broker.create(type=eventsys.TOUCH, ...)`

## Vendoring drivers

Use `scripts/vendor_circuitpython_drivers.py` to refresh Adafruit displayio drivers from GitHub.

```bash
python3 scripts/vendor_circuitpython_drivers.py --all
```

## pydevices priority

1. `i2cbus` — OLED FeatherWings, QT Py OLED
2. `rgbframebuffer` — Qualia / RGB parallel (RGB666)
3. `rgbmatrix` — MatrixPortal HUB75
4. `displaysys.epaperdisplay` — full MP backend
5. NeoPixel grid mapper for `PixelDisplay`
6. MIPI DSI host (SoC-specific)
