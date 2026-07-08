"""Adafruit CLUE ST7789 — MicroPython (nRF52840)"""

from spibus import SPIBus
from st7789 import ST7789

import eventsys

display_bus = SPIBus(
    id=0,
    baudrate=24_000_000,
    sck=4,
    mosi=5,
    miso=7,
    dc=29,
    cs=30,
    reset=31,
)

display_drv = ST7789(
    display_bus,
    width=240,
    height=240,
    colstart=0,
    rowstart=80,
    rotation=0,
    mirrored=False,
    color_depth=16,
    bgr=False,
    reverse_bytes_in_word=True,
    cp={
        "width": 240,
        "height": 240,
        "rotation": 0,
        "colstart": 0,
        "rowstart": 80,
        "bgr": False,
        "reverse_bytes_in_word": True,
    },
)
runtime = None
