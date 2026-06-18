# Minimum pydisplay on Wokwi (ESP32-S3 + ILI9341 + touch)

Installs core packages and runs `hello.py`.

## Files

- `main.py` — mip install + hello
- `diagram.json` — wiring for [`wokwi_ili9341_ft6x36_esp32s3`](../../board_configs/busdisplay/spi/wokwi_ili9341_ft6x36_esp32s3/)
- `wokwi.toml` — VS Code simulator config (requires firmware in [`../firmware/`](../firmware/))

## Quick test on wokwi.com

Copy `main.py` and `diagram.json` into a [new ESP32-S3 MicroPython project](https://wokwi.com/projects/new/micro-python-esp32-s3) and start the simulation.
