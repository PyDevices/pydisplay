# Driver inventory

Status of display and touch drivers vendored into pydisplay from Adafruit and Community bundles.

Regenerate display drivers:

```bash
python3 scripts/vendor_circuitpython_drivers.py --all
```

## SPI / I80 TFT (BusDisplay)

| File | Source | Status |
|------|--------|--------|
| `gc9a01.py` | Adafruit GC9A01A | in repo |
| `gc9d01.py` | Adafruit / community | in repo |
| `hx8357.py` | Adafruit | in repo |
| `ili9163.py` | Adafruit / Electronut | in repo |
| `ili9341.py` | Adafruit | in repo |
| `ili9488.py` | Adafruit | in repo |
| `st7735.py` | Adafruit | in repo |
| `st7735r.py` | Adafruit | in repo |
| `st7735r_1.py` | variant | in repo |
| `st7789.py` | Adafruit | in repo |
| `st7789vw.py` | variant | in repo |
| `st7796.py` | Adafruit | in repo |
| `st7701.py` | LilyGO T-RGB | in repo (`run_init` + `t-rgb_480` board config; pixel bus via displayif `rgbframebuffer`) |
| `ra8875.py` | Adafruit | skipped (framebuf API, not displayio) |

## OLED (BusDisplay)

| File | Source | Status |
|------|--------|--------|
| `sh1106.py` | Adafruit DisplayIO | vendored |
| `sh1107.py` | Adafruit DisplayIO | vendored |
| `ssd1305.py` | Adafruit DisplayIO | vendored |
| `ssd1306.py` | Adafruit DisplayIO | vendored |
| `ssd1322.py` | Adafruit | vendored |
| `ssd1325.py` | Adafruit | vendored |
| `ssd1327.py` | Adafruit | vendored |
| `ssd1331.py` | Adafruit | vendored |
| `ssd1351.py` | Adafruit | vendored |

## E-paper (EPaperDisplay on CP; epaperdisplay_chip on MP)

| File | Source | Status |
|------|--------|--------|
| `epaperdisplay_chip.py` | pydisplay MP shim | in repo |
| `digitalio.py` | pydisplay MP shim (`drivers/bus/`) | in repo |
| `ssd1680.py` | Adafruit | vendored |
| `ssd1681.py` | Adafruit | vendored |
| `ssd1683.py` | Adafruit | vendored |
| `ssd1675.py` | Adafruit | vendored |
| `ssd1677.py` | Adafruit | vendored |
| `ssd1608.py` | Adafruit | vendored |
| `uc8151d.py` | Adafruit | vendored |
| `uc8179.py` | Adafruit | vendored |
| `uc8253.py` | Adafruit | vendored |
| `il0373.py` | Adafruit | vendored |
| `il0398.py` | Adafruit | vendored |
| `il91874.py` | Adafruit | vendored |
| `ek79686.py` | Adafruit | vendored |
| `jd79661.py` | Adafruit | vendored |
| `jd79667.py` | Adafruit | vendored |
| `spd1656.py` | Adafruit | vendored |
| `acep7in.py` | Adafruit | vendored |

## Other

| File | Source | Status |
|------|--------|--------|
| `pcd8544.py` | Adafruit | vendored |
| `community/st7565.py` | Community DisplayIO | vendored |
## Input

| File | Source | Status |
|------|--------|--------|
| `keypad_gpio.py` | pydisplay | in repo |
| `keypad_shift.py` | pydisplay (74HC165) | in repo |

## Touch

| File | Source | Status |
|------|--------|--------|
| `ft6x36.py` | pydisplay MP | in repo |
| `tt21100.py` | pydisplay MP | in repo |
| `stmpe610.py` | pydisplay MP (SPI) | in repo |
| `xpt2046.py` | pydisplay MP | in repo |
| `gt911.py` | pydisplay MP | in repo |
| `cst8xx.py` | pydisplay MP | in repo |
| `cst226.py` | pydisplay MP | in repo |
| `chsc6x.py` | pydisplay MP | in repo |
| `circuitpython/adafruit_focaltouch.py` | Adafruit shim | in repo |
| `circuitpython/adafruit_ft5336.py` | Adafruit | vendored |
| `circuitpython/adafruit_tsc2007.py` | Adafruit | vendored |
| `circuitpython/adafruit_tt21100.py` | Adafruit | vendored |
| `circuitpython/adafruit_stmpe610.py` | Adafruit | vendored |
| `circuitpython/adafruit_touchscreen.py` | Adafruit 4-wire | vendored |
