"""Adafruit PyGamer ST7789 — MicroPython (SAMD51)"""

from spibus import SPIBus
from st7789 import ST7789

import eventsys

display_bus = SPIBus(
    id=0,
    baudrate=24_000_000,
    sck=13,
    mosi=11,
    miso=12,
    dc=39,
    cs=7,
    reset=47,
)

display_drv = ST7789(
    display_bus,
    width=160,
    height=128,
    colstart=0,
    rowstart=0,
    rotation=0,
    mirrored=False,
    color_depth=16,
    bgr=False,
    reverse_bytes_in_word=True,
)

broker = eventsys.Broker()
broker.register_quit_cleanup(display_drv)
