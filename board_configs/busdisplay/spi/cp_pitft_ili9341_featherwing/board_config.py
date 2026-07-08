"""Adafruit PiTFT 2.4" FeatherWing ILI9341 + STMPE610 — CircuitPython"""

from adafruit_stmpe610 import Adafruit_STMPE610_SPI
import board
from displayio import release_displays
from fourwire import FourWire
from ili9341 import ILI9341

import eventsys

release_displays()

display_bus = FourWire(
    board.SPI(),
    command=board.D10,
    chip_select=board.D9,
    baudrate=24_000_000,
    reset=board.D6,
)

display_drv = ILI9341(
    display_bus,
    width=240,
    height=320,
    colstart=0,
    rowstart=0,
    rotation=90,
    mirrored=False,
    color_depth=16,
    bgr=True,
    reverse_bytes_in_word=True,
)
_PITFT_CALIBRATION = ((357, 3_812), (390, 3_555))

touch_drv = Adafruit_STMPE610_SPI(
    board.SPI(),
    board.D8,
    baudrate=1000000,
    calibration=_PITFT_CALIBRATION,
    size=(display_drv.width, display_drv.height),
    disp_rotation=display_drv.rotation,
)


def touch_read_func():
    if touch_drv.touched:
        point = touch_drv.touch_point
        if point is not None:
            return point[0], point[1]
    return None


touch_rotation_table = (0, 0, 0, 0)

runtime = eventsys.Runtime(
    display=display_drv,
    touch_read=touch_read_func,
    touch_rotation_table=touch_rotation_table,
)
