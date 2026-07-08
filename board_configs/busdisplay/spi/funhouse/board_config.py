"""Adafruit FunHouse ST7789 + TT21100 — MicroPython (ESP32-S2)"""

from machine import I2C, Pin
from spibus import SPIBus
from st7789 import ST7789
from tt21100 import TT21100

import eventsys

display_bus = SPIBus(
    id=1,
    baudrate=24_000_000,
    sck=36,
    mosi=35,
    miso=-1,
    dc=39,
    cs=40,
    reset=41,
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
)
i2c = I2C(0, sda=Pin(34), scl=Pin(33), freq=400_000)
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
