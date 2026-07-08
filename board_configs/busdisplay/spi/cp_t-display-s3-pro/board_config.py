"""LilyGO T-Display-S3 Pro 222x480 ST7796 — CircuitPython"""

from adafruit_focaltouch import Adafruit_FocalTouch
import board
from displayio import release_displays
from fourwire import FourWire
from st7796 import ST7796

import eventsys

release_displays()

display_bus = FourWire(
    board.SPI(),
    command=board.GP9,
    chip_select=board.GP39,
    baudrate=60_000_000,
    reset=board.GP47,
)

display_drv = ST7796(
    display_bus,
    width=222,
    height=480,
    colstart=49,
    rowstart=0,
    rotation=0,
    mirrored=False,
    color_depth=16,
    bgr=True,
    reverse_bytes_in_word=True,
    invert=True,
    brightness=1.0,
    backlight_pin=board.GP48,
    backlight_on_high=True,
    reset_high=False,
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
