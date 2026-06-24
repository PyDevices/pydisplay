# pydisplay on Wokwi (ESP32-S3 + ILI9341 touch)

Browser project for [wokwi.com](https://wokwi.com): bundle + Wokwi board config + [`pydisplay_demo`](../src/examples/pydisplay_demo.py).

**Guide:** [Wokwi simulator](../docs/guides/wokwi.md) · **Hardware:** [Wokwi reference](../docs/hardware/wokwi.md)

Board config: [`wokwi_ili9341_ft6x36_esp32s3`](../board_configs/busdisplay/spi/wokwi_ili9341_ft6x36_esp32s3/)

## Files

| File | Purpose |
|------|---------|
| `main.py` | WiFi + `mip.install` (with `target="."`) + `pydisplay_demo` |
| `diagram.json` | ESP32-S3 + `board-ili9341-cap-touch` wiring |
| `pydisplay-bundle.json` | Slim MCU lib manifest (generated from `packages/pydisplay-bundle.json`) |

## Run in the browser

1. Create a [new ESP32-S3 MicroPython project](https://wokwi.com/projects/new/micropython-esp32-s3).
2. Replace the project's **main.py** and **diagram.json** with the files from this directory.
3. Start the simulation. Serial shows `mip` downloads, then the demo UI appears.

## Quick try (default)

Use `main.py` as committed. On first boot, `mip` downloads packages from GitHub (network required). You should see the **pydisplay_demo** UI: Rotate / Color bar and scrolling tips.

## Full install

Uncomment the two `add_ons` and `examples` lines in `main.py`, then restart the simulation. First boot takes several minutes.

Enables the full example catalog (`hello.py`, `bmp565_*`, `pydisplay_demo_async`, LVGL prep examples, and more under `examples/`).

## Wiring (GPIO)

| Signal | GPIO |
|--------|------|
| SPI SCK | 36 |
| SPI MOSI | 35 |
| SPI MISO | 37 |
| Display D/C | 16 |
| Display CS | 5 |
| Touch I2C SDA | 7 |
| Touch I2C SCL | 6 |

Matches [`wokwi_ili9341_ft6x36_esp32s3/board_config.py`](../board_configs/busdisplay/spi/wokwi_ili9341_ft6x36_esp32s3/board_config.py).
