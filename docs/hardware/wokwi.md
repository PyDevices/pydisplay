# Wokwi

Try pydisplay in the browser simulator without hardware.

## Hosted projects

| Project | Description |
|---------|-------------|
| [415770470006384641](https://wokwi.com/projects/415770470006384641) | Full PyDisplay ESP32-S3 example — uses `installer.py` |
| [404248867674669057](https://wokwi.com/projects/404248867674669057) | Minimum configuration (displaysys + eventsys + board config) |

## In-repo board configs

These match the Wokwi ILI9341 + ESP32-S3 setups:

| Config | Touch |
|--------|-------|
| `board_configs/busdisplay/spi/wokwi_ili9341_ft6x36_esp32s3` | FT6X36 |
| `board_configs/busdisplay/spi/wokwi_ili9341_esp32s3_no_touch` | None |

Install:

```python
import mip
mip.install("github:PyDevices/pydisplay/board_configs/busdisplay/spi/wokwi_ili9341_ft6x36_esp32s3")
```

## installer.py on Wokwi

The full example project downloads and runs [`installer.py`](../installation/installer.md) to pull micropython-lib and GitHub packages automatically.

## Known issues

`touch_keypad.py` notes occasional Wokwi `IndexError` when touching the last keypad row — simulator quirk, not necessarily hardware.

## Local Wokwi projects

This repo does not include `wokwi.toml` or `diagram.json`. Fork the hosted projects or create a new Wokwi project and point MIP installs at the board config paths above.
