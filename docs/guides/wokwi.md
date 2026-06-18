# Wokwi quick start

**Who:** You want to run pydisplay in the browser simulator without hardware or a local clone.

**Prerequisites:** A [wokwi.com](https://wokwi.com) account (free).

## Minimum project (recommended)

In-repo files: [`wokwi/minimum/`](https://github.com/PyDevices/pydisplay/tree/main/wokwi/minimum)

1. Create a [new ESP32-S3 MicroPython project](https://wokwi.com/projects/new/micropython-esp32-s3).
2. Copy `main.py` and `diagram.json` from `wokwi/minimum/`.
3. Start the simulation — `hello.py` should appear on the ILI9341 display.

Or open the [hosted minimum project](https://wokwi.com/projects/404248867674669057).

## Full install project

[`wokwi/esp32-s3-full/`](https://github.com/PyDevices/pydisplay/tree/main/wokwi/esp32-s3-full) downloads and runs `installer.py` with the Wokwi board config. Hosted copy: [415770470006384641](https://wokwi.com/projects/415770470006384641).

## VS Code

See [`wokwi/README.md`](https://github.com/PyDevices/pydisplay/blob/main/wokwi/README.md) for the Wokwi VS Code extension and firmware setup.

## Board configs used

| Config | Touch |
|--------|-------|
| `board_configs/busdisplay/spi/wokwi_ili9341_ft6x36_esp32s3` | FT6X36 |
| `board_configs/busdisplay/spi/wokwi_ili9341_esp32s3_no_touch` | None |

## Next

- [ESP32 board guide](esp32-board.md) — same steps on real hardware
- [Try pydisplay](../try/index.md) — PyScript browser demo
- [Wokwi details](../hardware/wokwi.md) — hosted legacy projects, known issues

## Reference

- [API reference (core)](../reference/)
