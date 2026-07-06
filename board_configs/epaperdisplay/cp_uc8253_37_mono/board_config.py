"""Adafruit UC8253 3.7" monochrome bare display — CircuitPython"""

import board
from displayio import release_displays
from fourwire import FourWire
from uc8253 import UC8253

from displaysys.epaperdisplay import EPaperDisplay
import eventsys

release_displays()

display_bus = FourWire(
    board.SPI(),
    command=board.D9,
    chip_select=board.D10,
    reset=board.D6,
    baudrate=4_000_000,
)

_epaper = UC8253(
    display_bus,
    width=416,
    height=240,
    busy_pin=board.D7,
    rotation=0,
)

display_drv = EPaperDisplay(_epaper, width=416, height=240, color_depth=1)

broker = eventsys.Broker()
broker.register_quit_cleanup(display_drv)
