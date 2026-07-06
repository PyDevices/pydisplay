# Board configs

Every pydisplay app needs a `board_config.py` that wires up the display, touch/input devices, and optional brokers.

## What board_config.py provides

Typically:

- A `display_drv` object (BusDisplay, SDLDisplay, PGDisplay, FBDisplay, etc.)
- Touch/read functions or `eventsys` brokers for input
- Optional setup (WiFi, sensors, backlight pins)

Configs live under [`board_configs/`](https://github.com/PyDevices/pydisplay/tree/main/board_configs). Each directory with a `package.json` can be installed via MIP:

```python
mip.install("github:PyDevices/pydisplay/board_configs/busdisplay/i80/t-display-s3")
```

## Picking a config

Match in priority order:

1. **Bus type** — SPI vs I80 (parallel)
2. **Display controller** — ILI9341, ST7789, GC9A01, …
3. **Touch controller** — FT6X36, XPT2046, …
4. **Microcontroller** — ESP32-S3, RP2040, …

An exact match for all four is rare; bus + display controller is usually enough to adapt.

## SPI bus configs

| Directory | Hardware |
|-----------|----------|
| `busdisplay/spi/wokwi_ili9341_ft6x36_esp32s3` | Wokwi ESP32-S3 + ILI9341 + touch |
| `busdisplay/spi/wokwi_ili9341_esp32s3_no_touch` | Wokwi ESP32-S3 + ILI9341 |
| `busdisplay/spi/t-display-s3-pro` | LilyGO T-Display S3 Pro |
| `busdisplay/spi/t-display-s3` | (I80 variant under `i80/t-display-s3`) |
| `busdisplay/spi/t-dongle-s3` | LilyGO T-Dongle S3 |
| `busdisplay/spi/t-embed` | LilyGO T-Embed |
| `busdisplay/spi/t-qt-pro` | LilyGO T-QT Pro |
| `busdisplay/spi/m5stack-cores3` | M5Stack CoreS3 |
| `busdisplay/spi/wt32sc01-plus` | (I80 under `i80/wt32sc01-plus`) |
| `busdisplay/spi/ili9341_eyespi_qtpy_esp32s3` | Adafruit ESP32-S3 QT Py + EyeSPI ILI9341 |
| `busdisplay/spi/ili9341_eyespi_qtpy_rp2040` | QT Py RP2040 + EyeSPI ILI9341 |
| `busdisplay/spi/ili9341_pico_uno` | Pico + UNO-style shield |
| `busdisplay/spi/cp_esp32_pico_eyespi_ili9341` | CircuitPython ESP32-Pico + ILI9341 |
| `busdisplay/spi/diy_esp32_ili9341_xpt2046` | DIY ESP32 + ILI9341 + XPT2046 |
| `busdisplay/spi/esp32_wrover_e_st7789_joystick` | ESP32 WROVER-E + ST7789 + joystick |
| `busdisplay/spi/seeed_gc9a01_on_qtpy_esp32s3` | GC9A01 round display on QT Py ESP32-S3 |
| `busdisplay/spi/seeed_gc9a01_on_qtpy_rp2040` | GC9A01 on QT Py RP2040 |
| `busdisplay/spi/pico-lcd-1.8` | Pico LCD 1.8" |
| `busdisplay/spi/rp2040-touch-lcd-1.28` | RP2040 1.28" round LCD |
| `busdisplay/spi/odroid_go` | ODROID-GO |

## I80 (parallel) bus configs

| Directory | Hardware |
|-----------|----------|
| `busdisplay/i80/t-display-s3` | LilyGO T-Display S3 |
| `busdisplay/i80/t-hmi` | LilyGO T-HMI |
| `busdisplay/i80/wt32sc01-plus` | Sunton WT32-SC01 Plus |
| `busdisplay/i80/ili9341_i80_rp2040` | RP2040 + ILI9341 I80 |
| `busdisplay/i80/bpi-centi-s3` | BPI Centi-S3 |

## Framebuffer / special configs

| Directory | Hardware |
|-----------|----------|
| `fbdisplay/qualia_tl040hds20` | MicroPython Qualia RGB |
| `fbdisplay/cp_qualia_tl040hds20` | CircuitPython Qualia |
| `fbdisplay/cp_usb_video` | CircuitPython USB Video |
| `fbdisplay/cp_matrixportal_s3_64x64` | MatrixPortal S3 HUB75 64×64 |
| `fbdisplay/matrixportal_s3_64x64` | MP skeleton (rgbmatrix cmod) |

## Pixel / addressable LED configs

| Directory | Hardware |
|-----------|----------|
| `pixeldisplay/cp_neopixel_8x8_zigzag` | NeoPixel 8×8 grid |
| `pixeldisplay/neopixel_8x8_zigzag` | MP skeleton |

## E-paper configs

| Directory | Hardware |
|-----------|----------|
| `epaperdisplay/cp_magtag` | Adafruit MagTag SSD1680 |
| `epaperdisplay/magtag` | MP skeleton |

## I2C OLED configs

| Directory | Hardware |
|-----------|----------|
| `busdisplay/i2c/cp_ssd1306_oled_featherwing` | FeatherWing OLED 128×32 |
| `busdisplay/i2c/ssd1306_oled_featherwing` | MP skeleton (i2cbus) |

## Built-in Adafruit boards (SPI)

| Directory | Hardware |
|-----------|----------|
| `busdisplay/spi/cp_pyportal` | PyPortal + TT21100 touch |
| `busdisplay/spi/cp_clue` | CLUE ST7789 |
| `busdisplay/spi/cp_*` | CircuitPython variants of MP configs |

## Desktop / browser configs

| Directory | Platform |
|-----------|----------|
| `sdldisplay` | CPython / MicroPython Unix — SDL2 (`SDLDisplay`) |
| `pgdisplay` | CPython — PyGame (`PGDisplay`) |
| `jndisplay` | Jupyter Notebook |
| `psdisplay` | PyScript browser |

## Default config

`src/lib/board_config.py` — auto-selected for desktop, PyScript, and Jupyter when no other config is installed.

## Custom config

Copy the closest match, edit pin assignments and driver imports, and test with `import pydisplay_demo` or `import displaysys_simpletest`. See the [**pydisplay_demo** guide](../examples/pydisplay_demo.md) for a walkthrough of the recommended smoke test.
