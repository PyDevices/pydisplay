"""QTPy ESP32S3 with EyeSPI and ILI9341 2.8" display — CircuitPython"""

from adafruit_focaltouch import Adafruit_FocalTouch
import board
from displayio import release_displays
from fourwire import FourWire
from ili9341 import ILI9341

import eventsys

release_displays()

display_bus = FourWire(
    board.SPI(),
    command=board.TX,
    chip_select=board.RX,
    baudrate=40_000_000,
)

display_drv = ILI9341(
    display_bus,
    colstart=0,
    rowstart=0,
    rotation=0,
    mirrored=False,
    color_depth=16,
    bgr=True,
    reverse_bytes_in_word=True,
    invert=False,
    width=240,
    height=320,
)
i2c = board.I2C()
touch_drv = Adafruit_FocalTouch(i2c)


def touch_read_func():
    touches = touch_drv.touches
    if len(touches):
        return touches[0]["x"], touches[0]["y"]
    return None


touch_rotation_table = (6, 3, 0, 5)

runtime = eventsys.Runtime(
    display=display_drv,
    touch_read=touch_read_func,
    touch_rotation_table=touch_rotation_table,
)
