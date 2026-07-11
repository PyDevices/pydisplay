# Wokwi simulator

Run pydisplay on a simulated ESP32-S3 with an ILI9341 capacitive touch display — no hardware required.

**In-repo project:** [`wokwi/`](../sim/wokwi/)

**Who:** You want MCU-faithful testing (SPI display, I2C touch, MicroPython `machine` APIs) without flashing a board.

**What you get:** [`testris`](https://github.com/PyDevices/pydisplay/blob/main/src/examples/testris.py) — a Tetris-style game driven by the on-screen touch keypad. One `main.py`; full example catalog = uncomment two lines.

**Prerequisites:**

- Network on first boot (`mip.install` pulls packages from GitHub)
- [wokwi.com](https://wokwi.com) account (free)

---

## Run in the browser

1. Create a [new ESP32-S3 MicroPython project](https://wokwi.com/projects/new/micropython-esp32-s3).
2. Replace **diagram.json** and **main.py** with the files from [`wokwi/`](../sim/wokwi/).
3. Start the simulation. Serial shows `mip` downloads, then `testris` appears.

**Full install:** uncomment the two `add_ons` / `examples` lines in `main.py` before starting (several-minute first boot).

The browser sim ships MicroPython — no local tools or firmware download needed.

---

## Quick vs full

| | **Quick (default)** | **Full** |
|--|---------------------|----------|
| **User action** | Use `main.py` as committed | Uncomment `add_ons` + `examples` lines |
| **First boot** | ~30 s | Several minutes |
| **Demo** | `testris` | Same + full `examples/` catalog |
| **Also enables** | — | `hello.py`, bmp565, `pydisplay_demo`, LVGL prep, etc. |

---

## Verify it worked

The `testris` game appears and responds to the on-screen touch keypad; serial has no `Traceback`.

---

## Board configs

| MIP package | Touch |
|-------------|-------|
| `board_configs/busdisplay/spi/wokwi_ili9341_ft6x36_esp32s3` | FT6X36 (default) |
| `board_configs/busdisplay/spi/wokwi_ili9341_esp32s3_no_touch` | None — use if touch is not wired |

Hardware details: [Wokwi reference](../hardware/wokwi.md).

---

## Next

- [ESP32 board guide](esp32-board.md) — same workflow on real hardware
- [Try pydisplay](../try/index.md) — PyScript browser demo
- [pydisplay_demo example](../examples/pydisplay_demo.md)
- [Desktop CPython](desktop-cpython.md)
