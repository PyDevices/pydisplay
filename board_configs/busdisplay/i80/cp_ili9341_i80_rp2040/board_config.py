"""Pico + ILI9341 I80 shield — CircuitPython"""

from adafruit_focaltouch import Adafruit_FocalTouch
import board
from displayio import release_displays
from ili9341 import ILI9341
from paralleldisplaybus import ParallelBus

import eventsys

release_displays()

display_bus = ParallelBus(
    board.GP0,
    board.GP1,
    board.GP2,
    board.GP3,
    board.GP4,
    board.GP5,
    board.GP6,
    board.GP7,
    board.GP14,
    board.GP15,
    board.GP13,
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
)
i2c = board.I2C()
touch_drv = Adafruit_FocalTouch(i2c)


def touch_read_func():
    touches = touch_drv.touches
    if len(touches):
        return touches[0]["x"], touches[0]["y"]
    return None


touch_rotation_table = None

runtime = eventsys.Runtime(
    display=display_drv,
    touch_read=touch_read_func,
    touch_rotation_table=touch_rotation_table,
)
