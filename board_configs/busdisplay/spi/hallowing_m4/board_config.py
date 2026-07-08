"""Adafruit HalloWing M4 ST7735 — MicroPython (SAMD51)"""

from spibus import SPIBus
from st7735 import ST7735

import eventsys

display_bus = SPIBus(
    id=0,
    baudrate=24_000_000,
    sck=22,
    mosi=55,
    miso=54,
    dc=63,
    cs=27,
    reset=62,
)

display_drv = ST7735(
    display_bus,
    width=240,
    height=240,
    colstart=0,
    rowstart=0,
    rotation=0,
    mirrored=False,
    color_depth=16,
    bgr=True,
    reverse_bytes_in_word=True,
)
runtime = None
