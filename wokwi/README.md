# Wokwi projects for pydisplay

In-repo [Wokwi](https://wokwi.com/) simulator projects for MicroPython on ESP32-S3 + ILI9341.

| Directory | Description |
|-----------|-------------|
| [`minimum/`](minimum/) | `displaysys` + `eventsys` + Wokwi board config + `hello` |
| [`esp32-s3-full/`](esp32-s3-full/) | Full install via `installer.py` (bundle, add_ons, examples) |

Board config (both projects): [`board_configs/busdisplay/spi/wokwi_ili9341_ft6x36_esp32s3/`](../../board_configs/busdisplay/spi/wokwi_ili9341_ft6x36_esp32s3/)

## Wokwi.com (browser)

1. Open [New ESP32-S3 MicroPython project](https://wokwi.com/projects/new/micropython-esp32-s3).
2. Replace **diagram.json** and **main.py** with the files from `minimum/` or `esp32-s3-full/` in this repo ([GitHub browse](https://github.com/PyDevices/pydisplay/tree/main/wokwi)).
3. Start the simulation. The sketch needs network access to download packages via `mip`.

Legacy hosted projects (same hardware intent): [minimum (404248867674669057)](https://wokwi.com/projects/404248867674669057), [full (415770470006384641)](https://wokwi.com/projects/415770470006384641).

## VS Code + Wokwi extension

1. Install [Wokwi for VS Code](https://marketplace.visualstudio.com/items?itemName=Wokwi.wokwi-vscode) and [mpremote](https://docs.micropython.org/en/latest/reference/mpremote.html).
2. Copy a MicroPython ESP32-S3 firmware `.bin` into [`firmware/`](firmware/) — see [`firmware/README.md`](firmware/README.md).
3. Open `wokwi/minimum/` or `wokwi/esp32-s3-full/` in VS Code.
4. **Wokwi: Start Simulator**, then upload and run:

```bash
mpremote connect port:rfc2217://localhost:4000 run main.py
```

Or copy `main.py` to the device filesystem and reset (see [Wokwi MicroPython VS Code guide](https://docs.wokwi.com/vscode/vscode-micropython)).

## Wiring

SPI and I2C pins match [`wokwi_ili9341_ft6x36_esp32s3/board_config.py`](../../board_configs/busdisplay/spi/wokwi_ili9341_ft6x36_esp32s3/board_config.py): SPI on GPIO 36/35/37/16/5, touch I2C on GPIO 7/6.
