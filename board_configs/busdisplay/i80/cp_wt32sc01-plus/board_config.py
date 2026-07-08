"""WT32-SC01 Plus 320x480 ST7796 I80 + FT6x36 — CircuitPython"""

from adafruit_focaltouch import Adafruit_FocalTouch
import board
from displayio import release_displays
from paralleldisplaybus import ParallelBus
from st7796 import ST7796

import eventsys

release_displays()

display_bus = ParallelBus(
    board.GP9,
    board.GP46,
    board.GP3,
    board.GP8,
    board.GP18,
    board.GP17,
    board.GP16,
    board.GP15,
    board.GP0,
    board.GP6,
    board.GP47,
)

display_drv = ST7796(
    display_bus,
    width=320,
    height=480,
    colstart=0,
    rowstart=0,
    rotation=0,
    mirrored=False,
    color_depth=16,
    bgr=True,
    reverse_bytes_in_word=True,
    invert=True,
    brightness=1.0,
    backlight_pin=board.GP45,
    backlight_on_high=True,
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
