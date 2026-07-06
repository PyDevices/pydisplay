# pydevices / cmods roadmap

MicroPython hardware gaps surfaced by pydisplay board configs. See also [display interfaces](display-interfaces.md).

## P0 — unblocks the most board configs

| Module | Repo target | Unblocks |
|--------|-------------|----------|
| `i2cbus` | pydevices/cmods | **Done in pydisplay** (`drivers/bus/i2cbus.py`) — OLED MP configs |
| `rgbframebuffer` | pydevices/cmods | `qualia_tl040hds20`, RGB parallel (RGB666) panels |

## P1 — LED matrix and fast parallel

| Module | Repo target | Unblocks |
|--------|-------------|----------|
| `rgbmatrix` | pydevices/cmods | `cp_matrixportal_s3_64x64`, `cp_matrixportal_m4_64x32` MP pairs |
| RP2040 PIO I80 | integrate `drivers/bus/_rp2_wip.py` | LilyGO I80 boards at speed |

## P2 — E-paper and addressable LEDs

| Work item | Location | Unblocks |
|-----------|----------|----------|
| `EPaperDisplay` buffer → panel push | `src/lib/displaysys/epaperdisplay.py` | **Done** — CP displayio + MP `bus.send`; chip base via `epaperdisplay_chip.py` |
| NeoPixel grid mapper | pydevices/cmods | `pixeldisplay/*` MP pairs |

## P3 — advanced interfaces

| Module | Notes |
|--------|-------|
| MIPI DSI host | SoC-specific (ESP32-P4, i.MX RT) |
| `picodvi` | RP2040 HDMI/DVI out |
| RA8875 parallel TFT | Legacy framebuf driver; needs adapter or new backend |

## pydisplay-side work (no cmod required)

- [x] `i2cbus` for MicroPython OLED (`drivers/bus/i2cbus.py`)
- [x] `EPaperDisplay.show()` — displayio push on CP; `bus.send` fallback on MP
- [x] `board.DISPLAY` adapter (`displaysys.boarddisplay.BoardDisplay`)
- [x] `epaperdisplay_chip` + `digitalio` shims for MP e-paper chip drivers
- [ ] Hardware validation pass on physical boards
- [ ] circup / micropython-lib publish for new drivers
