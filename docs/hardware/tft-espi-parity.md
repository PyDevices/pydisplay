# TFT_eSPI parity (Arduino) vs pydisplay / displayif

[TFT_eSPI](https://github.com/Bodmer/TFT_eSPI) is an Arduino graphics library with per-board `User_Setup` pin tables and many chip drivers. pydisplay splits the same problem across **bus drivers**, **chip drivers**, and **displayif** accelerated scanout.

This document states what is **implemented**, what uses **Python fallbacks**, and what is **out of scope** (document only).

## Bus-level mapping

| TFT_eSPI mode | pydisplay (Python) | displayif (MicroPython C) | Notes |
|---------------|-------------------|---------------------------|-------|
| SPI (`SPI_FREQUENCY`, `TFT_*`) | `spibus.SPIBus` + chip driver (`ili9341`, `st7789`, …) | `spibus` cmod | Full parity for SPI TFT init + pixel push via `BusDisplay` |
| 8-bit parallel 8080 (`TFT_D0`…`TFT_D7`, `TFT_WR`) | `drivers/bus/i80bus.py` (viper GPIO bitbang) | **rp2:** PIO+DMA `i80bus`; **esp32-S3:** `esp_lcd` I80; **mimxrt1062:** FlexIO MCULCD; **samd51:** GPIO bitbang (`common/i80bus`) | Native path preferred when flashed; Python path works without displayif |
| 16-bit parallel | — | **esp32-S3** `i80bus` only | TFT_eSPI 16-bit setups map to esp32 native driver, not Python |
| RGB / DPI parallel | — | `rgbframebuffer` (esp32 RGB LCD, mimxrt1062 eLCDIF) | Not in TFT_eSPI for RP2040; Qualia / RK043 class panels |
| — | — | `rgbmatrix`, `picodvi`, `mipidsi` | Not TFT_eSPI scope (HUB75, DVI/HSTX, MIPI DSI) |

## RP2040 / RP2350

| Capability | Status |
|------------|--------|
| SPI TFT | **Done** — `spibus` + vendored chip drivers; board configs under `busdisplay/spi/` |
| 8-bit I80 | **Done (native)** — displayif `i80bus` PIO+DMA on rp2; example `ili9341_i80_rp2040` |
| 8-bit I80 (Python) | **Done** — `i80bus.py` + `gpio_pin` (RP2040 SIO); RP2350 uses same SIO base |
| RGB parallel | **N/A** — no RP DPI peripheral; use SPI/I80 or **picodvi** (DVI) |
| MIPI DSI | **N/A** — RP2350 has **HSTX (DVI)**, not DSI; use `picodvi` + HSTX board configs |
| DVI / HSTX | **Done** — `picodvi` (RP2040 PIO libdvi, RP2350 HSTX); configs: `pico2_dvi_sock`, `pimoroni_pico_dv_base`, `adafruit_metro_rp2350_hstx_640x480` |

`drivers/bus/_rp2_wip.py` was an early PIO experiment — **superseded** by displayif `i80bus`; not wired from board configs.

## ESP32 (S2/S3/C3/P4, …)

| Capability | Status |
|------------|--------|
| SPI TFT | **Done** — `spibus` + chip drivers |
| 8-bit I80 | **Done (S3)** — displayif `i80bus`; configs e.g. `t-display-s3`, `wt32sc01-plus` |
| RGB parallel | **Done (RGB LCD SoCs)** — displayif `rgbframebuffer`; Qualia, `t-rgb_480` |
| MIPI DSI | **Done (P4)** — displayif `mipidsi`; Waveshare 4B, M5 Tab5 MP config |
| HUB75 | **Done (S3)** — displayif `rgbmatrix` Protomatter |

**PSRAM:** large `rgbframebuffer` / `mipidsi` framebuffers need `CONFIG_SPIRAM` in sdkconfig — `cmods/build_mp.sh` warns before esp32 builds when displayif is present.

## mimxrt (1062 / 1176)

| Capability | Status |
|------------|--------|
| SPI / I2C | **Done** — `spibus`, `i2cbus` |
| 8-bit I80 | **Done (1062)** — FlexIO `i80bus` |
| RGB parallel | **Done (1062)** — eLCDIF `rgbframebuffer`; RK043 EVK config |
| MIPI DSI | **Done (1176)** — `mipidsi` + TC358762 bridge; Waveshare 5″ DSI EVK config |
| HUB75 | **Done (1062)** — `rgbmatrix` Protomatter |

## samd (SAMD51)

| Capability | Status |
|------------|--------|
| SPI / I2C | **Done** |
| 8-bit I80 | **Done (SAMD51)** — GPIO bitbang via `common/i80bus/gpio_bitbang.c` |
| RGB / DSI | **N/A** — stubs only; no SoC DPI/DSI |
| HUB75 | **Done** — `rgbmatrix` Protomatter (Matrix Portal M4 configs) |

## Chip drivers (TFT_eSPI `SetupNNN_*`)

TFT_eSPI bundles dozens of controller init tables. pydisplay **vendors CircuitPython displayio chip drivers** (`ili9341`, `st7701`, `gc9a01`, …) and wires them through `BusDisplay` / `EPaperDisplay` — equivalent role, different file layout. Adding a new panel is a **driver + board_config** pair, not a `User_Setup.h` edit.

## Board config coverage (MP + CP)

| Board | MP | CP |
|-------|----|----|
| M5 Tab5 ILI9881C (early) | `m5stack_tab5_ili9881c` | `cp_m5stack_tab5_ili9881c` |
| M5 Tab5 ST7123 (current) | `m5stack_tab5_st7123` | — |
| Pico 2 DVI Sock (HSTX) | `pico2_dvi_sock_640x480` | `cp_pico2_dvi_sock_640x480` |
| Metro RP2350 HSTX | `adafruit_metro_rp2350_hstx_640x480` | `cp_adafruit_metro_rp2350_hstx_640x480` |
| Pimoroni Pico DV (RP2040 PIO) | `pimoroni_pico_dv_base_640x480` | `cp_pimoroni_pico_dv_base_640x480` |
| LilyGO T-RGB | `t-rgb_480` | — (MP-focused) |

## When not to port TFT_eSPI features

- **ESP8266** — out of pydisplay scope
- **AVR** — out of scope
- **PSRAM-less ESP32** large framebuffers — hardware limit; use smaller buffers or SPI TFT
- **ST7123 Tab5** on MicroPython — use `m5stack_tab5_st7123`; hardware validation pending
