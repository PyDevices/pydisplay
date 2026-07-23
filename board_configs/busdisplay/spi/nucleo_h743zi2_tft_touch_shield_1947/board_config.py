"""NUCLEO-H743ZI2 + Adafruit 2.8\" TFT Touch Shield (cap) product 1947.

ILI9341 SPI, CS=D10 DC=D9. FT6206 on I2C(1) (Arduino D14/D15).

Shield SPI jumpers (same as Metro bring-up):
  SoftSPI: solder 11/SO/SI (D11-D13), cut ICSP.
  HW SPI:  SPI(1) is already on Arduino D13/D11/D12 (PA5/PB5/PA6) — works
           with 11/SO/SI jumpers (unlike Metro). Prefer HW; SoftSPI is too slow.

Note: board pins.csv maps D13→PA5 (ST Arduino SCK). Pin("A5") is Arduino
analog A5 (PF10) — do not use it for SPI.
"""

import gc

from ft6x36 import FT6x36
from ili9341 import ILI9341
from machine import I2C, Pin
from spibus import SPIBus

import eventsys

# SoftSPI is too slow for games; HW SPI1 shares Arduino header pins.
USE_SOFTSPI = False

# Hold SD CS high when the microSD socket is unused.
Pin("D4", Pin.OUT, value=1)

gc.collect()

if USE_SOFTSPI:
    display_bus = SPIBus(
        soft=True,
        baudrate=4_000_000,
        sck="D13",
        mosi="D11",
        miso="D12",
        dc="D9",
        cs="D10",
    )
else:
    # SPI(1) defaults are Arduino D13/D11/D12; native spibus rejects pin kwargs here.
    display_bus = SPIBus(
        id=1,
        baudrate=24_000_000,
        dc="D9",
        cs="D10",
    )

display_drv = ILI9341(
    display_bus,
    width=240,
    height=320,
    colstart=0,
    rowstart=0,
    rotation=0,
    mirrored=False,
    color_depth=16,
    bgr=True,
    reverse_bytes_in_word=True,
    invert=False,
    brightness=1.0,
    backlight_pin=None,
    backlight_on_high=True,
    reset_pin=None,
    reset_high=True,
    power_pin=None,
    power_on_high=True,
)

gc.collect()

i2c = I2C(1, freq=100_000)
touch_drv = FT6x36(i2c)
touch_read_func = touch_drv.get_positions
touch_rotation_table = (6, 3, 0, 5)

runtime = eventsys.Runtime(
    display=display_drv,
    touch_read=touch_read_func,
    touch_rotation_table=touch_rotation_table,
)
