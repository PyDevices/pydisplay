# Wokwi hardware reference

Technical reference for the in-repo Wokwi project. For setup steps, see **[Wokwi simulator guide](../guides/wokwi.md)**.

## Project layout

| Path | Role |
|------|------|
| [`wokwi/`](https://github.com/PyDevices/pydisplay/tree/main/sim/wokwi) | `main.py`, `diagram.json` — MCU lib + `testris` |

---

## Simulated hardware

| Item | Detail |
|------|--------|
| MCU | ESP32-S3 DevKitC-1 (`board-esp32-s3-devkitc-1`), 16 MB flash |
| Display | ILI9341 240×320 via SPI (`board-ili9341-cap-touch`) |
| Touch | FT6206 I2C (simulated on the cap-touch board) |

### Pin wiring

Matches [`wokwi_ili9341_ft6x36_esp32s3/board_config.py`](https://github.com/PyDevices/pydisplay/blob/main/board_configs/busdisplay/spi/wokwi_ili9341_ft6x36_esp32s3/board_config.py):

| Signal | GPIO | `diagram.json` part / pin |
|--------|------|---------------------------|
| Power | 3V3 | `lcd1:VCC` → `esp:3V3.1` |
| SPI SCK | 36 | `lcd1:SCK` → `esp:36` |
| SPI MOSI | 35 | `lcd1:MOSI` → `esp:35` |
| SPI MISO | 37 | `lcd1:MISO` → `esp:37` |
| Display D/C | 16 | `lcd1:D/C` → `esp:16` |
| Display CS | 5 | `lcd1:CS` → `esp:5` |
| Touch I2C SDA | 7 | `lcd1:SDA` → `esp:7` |
| Touch I2C SCL | 6 | `lcd1:SCL` → `esp:6` |
| Backlight | 3V3 | `lcd1:LED` → `esp:3V3.1` |

Display part id in `diagram.json`: **`lcd1`** (`board-ili9341-cap-touch`).

---

## FT6206 (Wokwi) vs FT6X36 (pydisplay driver)

Wokwi’s cap-touch board simulates an **FT6206** I2C controller. pydisplay’s board config uses the **FT6X36** driver (`ft6x36.py`) — same FT6xx family and register-style protocol. No board_config change is expected; if touch behaves oddly, compare with real hardware and file an issue.

---

## Board `env` attribute (optional)

Committed `diagram.json` does **not** pin a MicroPython `env` string. Browser sims use built-in firmware.

If you need a specific MicroPython build, copy the current `env` value from the [ESP32-S3 MicroPython template](https://wokwi.com/projects/new/micropython-esp32-s3) into the DevKit `attrs` — do not commit a release-specific string in the repo.

---

## MIP install pattern

Matches [`wokwi/main.py`](https://github.com/PyDevices/pydisplay/blob/main/sim/wokwi/main.py):

```python
import mip

mip.install("github:PyDevices/pydisplay/sim/wokwi/mcu-lib.json", target=".")
mip.install(
    "github:PyDevices/pydisplay/board_configs/busdisplay/spi/wokwi_ili9341_ft6x36_esp32s3",
    target=".",
)  # last — installs root board_config.py
mip.install(
    "github:PyDevices/pydisplay/src/examples/testris.py",
    target=".",
)

import lib.path
import testris
```

**Full install on Wokwi:** uncomment the `add_ons` and `examples` `mip.install` lines in `main.py`.

**No-touch variant:**

```python
mip.install(
    "github:PyDevices/pydisplay/board_configs/busdisplay/spi/wokwi_ili9341_esp32s3_no_touch"
)
```

Use a display-only `diagram.json` (no touch I2C wires) with that config.

---

## Known issues

| Issue | Notes |
|-------|-------|
| `TouchKeypad` IndexError on last row | Wokwi simulator quirk; may not reproduce on hardware |
| Old hosted wokwi.com project IDs | May be stale; use in-repo [`wokwi/`](https://github.com/PyDevices/pydisplay/tree/main/sim/wokwi) |

See also [Troubleshooting](../troubleshooting.md).
