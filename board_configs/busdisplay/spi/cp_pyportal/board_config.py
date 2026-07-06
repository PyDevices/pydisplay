"""Adafruit PyPortal (built-in ILI9341 + TT21100 touch) — CircuitPython"""

from adafruit_tt21100 import TT21100
import board
from displayio import release_displays
from fourwire import FourWire
from ili9341 import ILI9341

import eventsys

release_displays()

display_bus = FourWire(
    board.SPI(),
    command=board.TFT_DC,
    chip_select=board.TFT_CS,
    reset=board.TFT_RESET,
    baudrate=24_000_000,
)

display_drv = ILI9341(
    display_bus,
    width=320,
    height=240,
    rotation=0,
    colstart=0,
    rowstart=0,
    bgr=True,
    reverse_bytes_in_word=True,
)

i2c = board.I2C()
touch_drv = TT21100(i2c)


def touch_read_func():
    touches = touch_drv.touches
    if len(touches):
        return touches[0]["x"], touches[0]["y"]
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
