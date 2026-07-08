"""DIY ESP32 ILI9341 + XPT2046 resistive touch — CircuitPython"""

from adafruit_touchscreen import Touchscreen
import board
from displayio import release_displays
from fourwire import FourWire
from ili9341 import ILI9341

import eventsys

release_displays()

display_bus = FourWire(
    board.SPI(),
    command=board.D5,
    chip_select=board.D15,
    reset=board.D4,
    baudrate=40_000_000,
)

display_drv = ILI9341(
    display_bus,
    width=240,
    height=320,
    colstart=0,
    rowstart=0,
    rotation=270,
    mirrored=False,
    color_depth=16,
    bgr=True,
    reverse_bytes_in_word=True,
    invert=False,
    power_pin=board.D22,
    power_on_high=True,
)

# XPT2046 on separate SPI — map to analog 4-wire touchscreen pins
touchscreen = Touchscreen(
    board.D25,
    board.D26,
    board.D27,
    board.D32,
    x_resistance=400,
)


def touch_read_func():
    point = touchscreen.touch_point
    if point:
        return point[0], point[1]
    return None


touch_rotation_table = (0, 0, 0, 0)

runtime = eventsys.Runtime(
    display=display_drv,
    touch_read=touch_read_func,
    touch_rotation_table=touch_rotation_table,
)
