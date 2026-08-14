# pydevices-examples on Wokwi (ESP32-S3 + ILI9341 touch)

Browser project for [wokwi.com](https://wokwi.com): PyDevices core + `pygraphics` + Wokwi board config + [`testris`](../../lib/examples/testris.py) (a touch + joystick Tetris demo).

**Guide:** [Wokwi simulator](../../docs/guides/wokwi.md) · **Hardware:** [Wokwi reference](https://pydevices.github.io/pydevices/wokwi.html)

Board config: [`wokwi_ili9341_ft6x36_esp32s3`](https://github.com/PyDevices/pydevices/tree/main/board_configs/busdisplay/spi/wokwi_ili9341_ft6x36_esp32s3)

## Files

| File | Purpose |
|------|---------|
| `main.py` | WiFi + `mip.install` (with `target="."`) + `testris` |
| `diagram.json` | ESP32-S3 + `board-ili9341-cap-touch` wiring |

## Run in the browser

1. Create a [new ESP32-S3 MicroPython project](https://wokwi.com/projects/new/micropython-esp32-s3).
2. Replace the project's **main.py** and **diagram.json** with the files from this directory.
3. Start the simulation. Serial shows `mip` downloads, then the demo UI appears.

## Quick try (default)

Use `main.py` as committed. On first boot, `mip` downloads PyDevices core + `pygraphics` from the PyDevices MIP index (network required). You should see the **testris** game running — drive it with the on-screen touch keypad.

## Full install

Uncomment the two `utils` and `examples` lines in `main.py`, then restart the simulation. First boot takes several minutes.

Enables the full example catalog (`hello.py`, `bmp565_*`, `pydevices_demo`, LVGL prep examples, and more under `examples/`).

## Wiring (GPIO)

| Signal | GPIO |
|--------|------|
| SPI SCK | 12 (SPI2 IOMUX) |
| SPI MOSI | 11 |
| SPI MISO | 13 |
| Display D/C | 16 |
| Display CS | 5 |
| Display LED / RST | 3V3 |
| Touch I2C SDA | 7 |
| Touch I2C SCL | 6 |

SPI baudrate **20 MHz**. Matches [`wokwi_ili9341_ft6x36_esp32s3/board_config.py`](https://github.com/PyDevices/pydevices/blob/main/board_configs/busdisplay/spi/wokwi_ili9341_ft6x36_esp32s3/board_config.py).
