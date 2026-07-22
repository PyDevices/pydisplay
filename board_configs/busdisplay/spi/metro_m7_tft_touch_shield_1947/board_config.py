"""Metro M7 + Adafruit 2.8\" TFT Touch Shield (cap) product 1947.

ILI9341 SPI, CS=D10 DC=D9. FT6206 on I2C(0). runtime=None (64KiB heap).

Toggle USE_SOFTSPI below when changing shield SPI jumpers:
  True  - solder 11/SO/SI (D11-D13), cut ICSP -> SoftSPI
  False - solder ICSP, cut 11/SO/SI -> hardware SPI(0)
"""

import gc

from ft6x36 import FT6x36
from ili9341 import ILI9341
from machine import I2C, Pin
from spibus import SPIBus

# Flip this after moving shield SPI jumpers (only change needed).
USE_SOFTSPI = True

Pin("ESP_CS", Pin.OUT, value=1)
Pin("D4", Pin.OUT, value=1)

gc.collect()

if USE_SOFTSPI:
    # Shield SPI on Arduino D11-D13 (bitbang; Metro cannot remap SPI0 here).
    display_bus = SPIBus(
        soft=True,
        baudrate=2_000_000,
        sck="D13",
        mosi="D11",
        miso="D12",
        dc="D9",
        cs="D10",
    )
else:
    # Shield SPI via ICSP / LPSPI1 = machine.SPI(0).
    display_bus = SPIBus(
        id=0,
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

i2c = I2C(0, freq=100_000)
touch_drv = FT6x36(i2c)
touch_read_func = touch_drv.get_positions
touch_rotation_table = (6, 3, 0, 5)
runtime = None
