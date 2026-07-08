"""Waveshare RP2040-Touch-LCD-1.28 GC9A01 — CircuitPython"""

from adafruit_focaltouch import Adafruit_FocalTouch
import board
from displayio import release_displays
from fourwire import FourWire
from gc9a01 import GC9A01

import eventsys

release_displays()

display_bus = FourWire(
    board.SPI(),
    command=board.GP8,
    chip_select=board.GP9,
    baudrate=60_000_000,
    reset=board.GP13,
)

display_drv = GC9A01(
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
    invert=True,
    brightness=1.0,
    backlight_pin=board.GP25,
    backlight_on_high=True,
)
i2c = board.I2C()
touch_drv = Adafruit_FocalTouch(i2c)


def touch_read_func():
    touches = touch_drv.touches
    if len(touches):
        return touches[0]["x"], touches[0]["y"]
    return None


touch_rotation_table = (0, 5, 6, 3)

runtime = eventsys.Runtime(
    display=display_drv,
    touch_read=touch_read_func,
    touch_rotation_table=touch_rotation_table,
)
