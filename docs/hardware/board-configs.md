# Board configs

Every pydisplay app needs a `board_config.py` that wires up the display, input devices, and optional [Runtime](../concepts/runtime.md).

## What board_config.py provides

Typically:

- A `display_drv` object (BusDisplay, SDLDisplay, PGDisplay, FBDisplay, etc.)
- A `runtime` object (`eventsys.Runtime(...)`) when the display needs periodic present or input dispatch; `None` on MCU display-only boards
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
| `fbdisplay/t-rgb_480` | LilyGO T-RGB 480×480 ST7701 (ESP32-S3; RGB via pydevices/displayif) |
| `fbdisplay/cp_qualia_tl040hds20` | CircuitPython Qualia |
| `fbdisplay/cp_usb_video` | CircuitPython USB Video |
| `fbdisplay/cp_matrixportal_s3_64x64` | MatrixPortal S3 HUB75 64×64 |
| `fbdisplay/matrixportal_s3_64x64` | MP skeleton (rgbmatrix cmod) |

## Pixel / addressable LED configs

| Directory | Hardware |
|-----------|----------|
| `pixeldisplay/cp_neopixel_8x4` | NeoPixel 8×4 grid (CircuitPython) |
| `pixeldisplay/neopixel_8x4` | NeoPixel 8×4 grid (MicroPython) |
| `pixeldisplay/cp_dotstar_12x6` | DotStar 12×6 grid (CircuitPython) |
| `pixeldisplay/dotstar_12x6` | DotStar 12×6 grid (MicroPython) |

Draw through `display_drv` only; `_pixel_framebuf` is an internal wiring detail.

## E-paper configs

| Directory | Hardware |
|-----------|----------|
| `epaperdisplay/cp_magtag` | Adafruit MagTag SSD1680 + KEYPAD |
| `epaperdisplay/magtag` | MagTag SSD1680 + KEYPAD (MP) |
| `epaperdisplay/cp_ssd1680_213_featherwing` | 2.13" E-Ink FeatherWing |
| `epaperdisplay/ssd1680_213_featherwing` | 2.13" E-Ink FeatherWing (MP) |
| `epaperdisplay/cp_acep7in_73` | ACeP 7.3" 7-color E-Ink |
| `epaperdisplay/acep7in_73` | ACeP 7.3" (MP) |
| `epaperdisplay/cp_ssd1675_213_featherwing` | SSD1675 2.13" monochrome FeatherWing |
| `epaperdisplay/ssd1675_213_featherwing` | SSD1675 2.13" FeatherWing (MP) |
| `epaperdisplay/cp_uc8151d_29_breakout` | UC8151D 2.9" flexible breakout |
| `epaperdisplay/uc8151d_29_breakout` | UC8151D 2.9" breakout (MP) |

Additional vendored chip drivers (each has `cp_*` sibling): `ssd1681_154_tricolor`, `ssd1683_213_featherwing`, `ssd1677_583_mono`, `ssd1608_154_mono`, `il0373_213_tricolor`, `il0398_42_mono`, `il91874_27_tricolor`, `uc8179_583_mono`, `uc8253_37_mono`, `ek79686_27_tricolor`, `jd79661_213_4gray`, `jd79667_391_4gray`, `spd1656_154_acep`.

Tri-color / 4-gray configs use `color_depth=2` (0=white, 1=black, 2=accent). ACeP configs use `color_depth=4`.

| Directory | Hardware |
|-----------|----------|
| `fbdisplay/cp_matrixportal_m4_64x32` | MatrixPortal M4 HUB75 64×32 |
| `busdisplay/spi/cp_hallowing_m4` | HalloWing M4 |
| `busdisplay/spi/cp_pyportal_titano` | PyPortal Titano + touch |
| `busdisplay/i2c/cp_sh1107_oled_128x64` | SH1107 OLED |
| `busdisplay/spi/cp_ssd1351_128_oled` | SSD1351 color OLED |

## I2C OLED configs

| Directory | Hardware |
|-----------|----------|
| `busdisplay/i2c/cp_ssd1306_oled_featherwing` | FeatherWing OLED 128×32 |
| `busdisplay/i2c/ssd1306_oled_featherwing` | FeatherWing OLED 128×32 (MP + `i2cbus`) |
| `busdisplay/i2c/sh1107_oled_128x64` | SH1107 OLED 128×64 (MP + `i2cbus`) |

## Built-in Adafruit boards (SPI)

| Directory | Hardware |
|-----------|----------|
| `busdisplay/spi/cp_pyportal` | PyPortal + TT21100 touch |
| `busdisplay/spi/pyportal` | PyPortal + TT21100 (MP SAMD51) |
| `busdisplay/spi/cp_pyportal_titano` | PyPortal Titano + touch |
| `busdisplay/spi/pyportal_titano` | PyPortal Titano (MP SAMD51) |
| `busdisplay/spi/cp_funhouse` | FunHouse ST7789 + touch |
| `busdisplay/spi/funhouse` | FunHouse ST7789 + TT21100 (MP ESP32-S2) |
| `busdisplay/spi/cp_pybadge` | PyBadge LC + buttons |
| `busdisplay/spi/pybadge` | PyBadge LC + shift-register KEYPAD (MP) |
| `busdisplay/spi/cp_hallowing_m4` | HalloWing M4 |
| `busdisplay/spi/hallowing_m4` | HalloWing M4 ST7735 (MP) |
| `busdisplay/spi/cp_pitft_ili9341_featherwing` | PiTFT FeatherWing + STMPE610 |
| `busdisplay/spi/pitft_ili9341_featherwing` | PiTFT FeatherWing (MP Feather + STMPE610) |
| `busdisplay/spi/clue` | CLUE ST7789 (MP nRF52840) |
| `busdisplay/spi/cp_clue` | CLUE ST7789 (CircuitPython) |
| `busdisplay/spi/cp_funhouse` | FunHouse ST7789 + touch |
| `busdisplay/spi/cp_pygamer` | PyGamer ST7789 |
| `busdisplay/spi/pygamer` | PyGamer ST7789 (MP SAMD51) |
| `busdisplay/spi/cp_pitft_ili9341_featherwing` | PiTFT FeatherWing + STMPE610 |
| `busdisplay/spi/cp_ssd1331_096_oled` | SSD1331 color OLED |
| `busdisplay/spi/ssd1331_096_oled` | SSD1331 color OLED (MP) |
| `busdisplay/spi/cp_ssd1351_128_oled` | SSD1351 color OLED |
| `busdisplay/spi/ssd1351_128_oled` | SSD1351 color OLED (MP) |
| `busdisplay/i80/cp_t-display-s3` | LilyGO T-Display S3 I80 |
| `busdisplay/i80/cp_t-hmi` | LilyGO T-HMI I80 + touch |
| `busdisplay/i80/cp_wt32sc01-plus` | WT32-SC01 Plus I80 |
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
