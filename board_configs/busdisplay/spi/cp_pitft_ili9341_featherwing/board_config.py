"""Adafruit PiTFT 2.4\" FeatherWing ILI9341 + STMPE610 — CircuitPython"""

from adafruit_stmpe610 import Adafruit_STMPE610
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

touch_drv = Adafruit_STMPE610(display_bus)


def touch_read_func():
    if touch_drv.touched:
        return touch_drv.touch_position
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
