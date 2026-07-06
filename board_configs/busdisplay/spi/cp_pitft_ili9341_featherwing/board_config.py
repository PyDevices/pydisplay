"""Adafruit PiTFT 2.4\" FeatherWing ILI9341 + STMPE610 — CircuitPython"""

from adafruit_stmpe610 import Adafruit_STMPE610_SPI
import board
from displayio import release_displays
from fourwire import FourWire
from ili9341 import ILI9341

import eventsys

release_displays()

# PiTFT 2.4" FeatherWing (#3315) STMPE610 calibration (rotation 90°)
_PITFT_CALIBRATION = ((357, 3812), (390, 3555))

display_bus = FourWire(
    board.SPI(),
    command=board.D10,
    chip_select=board.D9,
    reset=board.D6,
    baudrate=24_000_000,
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

touch_drv = Adafruit_STMPE610_SPI(
    board.SPI(),
    board.D8,
    baudrate=1_000_000,
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

broker = eventsys.Broker()

touch_dev = broker.create(
    type=eventsys.TOUCH,
    read=touch_read_func,
    data=display_drv,
    data2=touch_rotation_table,
)

broker.register_quit_cleanup(display_drv)
