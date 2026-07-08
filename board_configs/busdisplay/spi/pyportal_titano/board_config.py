"""Adafruit PyPortal Titano ILI9341 + TT21100 — MicroPython (SAMD51)"""

from ili9341 import ILI9341
from machine import I2C, Pin
from spibus import SPIBus
from tt21100 import TT21100

import eventsys

display_bus = SPIBus(
    id=0,
    baudrate=24_000_000,
    sck=13,
    mosi=12,
    miso=14,
    dc=41,
    cs=38,
    reset=0,
)

display_drv = ILI9341(
    display_bus,
    width=320,
    height=480,
    rotation=0,
    colstart=0,
    rowstart=0,
    bgr=True,
    reverse_bytes_in_word=True,
)
i2c = I2C(1, sda=Pin(34), scl=Pin(35), freq=400_000)
touch_drv = TT21100(i2c)


def touch_read_func():
    touches = touch_drv.touches
    if len(touches):
        return touches[0]["x"], touches[0]["y"]
    return None


touch_rotation_table = (0, 0, 0, 0)

runtime = eventsys.Runtime(
    display=display_drv,
    touch_read=touch_read_func,
    touch_rotation_table=touch_rotation_table,
)
