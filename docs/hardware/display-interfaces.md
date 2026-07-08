# Display interfaces

Maps hardware interface types to pydisplay `displaysys` backends and pydevices/displayif work for MicroPython parity.

## Interface matrix

| Interface | Industry term | CircuitPython module | displaysys backend | MicroPython bus | pydevices status |
|-----------|---------------|----------------------|-------------------|-----------------|------------------|
| SPI + MIPI DCS | SPI TFT | `fourwire.FourWire` + chip driver | **BusDisplay** | `SPIBus` | Done |
| 8080 8-bit parallel | I80 parallel | `paralleldisplaybus.ParallelBus` | **BusDisplay** | `I80Bus` | displayif + bit-bang |
| I2C DCS | I2C OLED | `i2cdisplaybus.I2CDisplayBus` | **BusDisplay** | `I2CBus` | Done |
| RGB parallel timed | RGB565 / **RGB666** | `dotclockframebuffer` | **FBDisplay** | `rgbframebuffer` | displayif (esp32, mimxrt1062) |
| HUB75 LED matrix | HUB75 | `rgbmatrix.RGBMatrix` | **FBDisplay** | `rgbmatrix` | displayif |
| WS2812 / DotStar grid | Addressable LED matrix | `adafruit_pixel_framebuf` | **PixelDisplay** | `displaysys.pixeldisplay.PixelFramebuffer` + neopixel | Done |
| SPI E-ink | E-paper | `epaperdisplay.EPaperDisplay` chip drivers | **EPaperDisplay** | SPI + chip driver | CP displayio push; MP bus.send path |
| USB UVC gadget | USB Video | `usb_video` | **FBDisplay** | N/A | CP only |
| MIPI DSI | MIPI DSI | `mipidsi` (SoC firmware) | **FBDisplay** | `mipidsi` | displayif (esp32-P4, mimxrt1176) |
| DVI (TMDS) | DVI | `picodvi` | **FBDisplay** | `picodvi` | displayif (rp2040/rp2350 HSTX) |

**Note:** MIPI **DCS** (Display Command Set) over SPI/I80 is not MIPI **DSI** (the high-speed serial panel interface). **RP2350 has no MIPI DSI** — use `picodvi` (HSTX) or SPI/I80 instead.

## Board config directories

| Backend | Path | Example |
|---------|------|---------|
| BusDisplay | `board_configs/busdisplay/{spi,i80,i2c}/` | `cp_pyportal`, `ili9341_eyespi_qtpy_esp32s3` |
| FBDisplay | `board_configs/fbdisplay/` | `qualia_tl040hds20`, `t-rgb_480`, `esp32-p4-wifi6-touch-lcd-4b` |
| PixelDisplay | `board_configs/pixeldisplay/` | `cp_neopixel_8x4`, `cp_dotstar_12x6` |
| EPaperDisplay | `board_configs/epaperdisplay/` | `cp_magtag` |

MicroPython RGB/HUB75/DSI/DVI drivers live in **pydevices/displayif**, wired from board configs and drivers vendored here in pydisplay. CircuitPython configs use `cp_*` prefixes and CP native modules.

## Touch

Touch controllers live in `drivers/touch/`. CircuitPython shims are under `drivers/touch/circuitpython/`. Every applicable `board_config.py` should wire touch via the runtime constructor:

```python
runtime = eventsys.Runtime(
    display=display_drv,
    touch_read=touch_drv.get_positions,
    touch_rotation_table=touch_rotation_table,  # when default mapping is wrong
)
```

See [Runtime — touch read contract](../concepts/runtime.md#touch-read-contract).

## Vendoring drivers

Use `scripts/vendor_circuitpython_drivers.py` to refresh Adafruit displayio drivers from GitHub.

```bash
python3 scripts/vendor_circuitpython_drivers.py --all
```

## pydevices priority

See also [TFT_eSPI parity](tft-espi-parity.md) for Arduino bus/driver mapping.

1. `i2cbus` — OLED FeatherWings, QT Py OLED
2. `rgbframebuffer` — Qualia / RGB parallel (RGB666)
3. `rgbmatrix` — MatrixPortal HUB75
4. `displaysys.epaperdisplay` — full MP backend
5. ~~NeoPixel grid mapper for `PixelDisplay`~~ — `displaysys.pixeldisplay.PixelFramebuffer` (MP) + Adafruit bundle (CP)
6. MIPI DSI host (SoC-specific — not RP2350)
