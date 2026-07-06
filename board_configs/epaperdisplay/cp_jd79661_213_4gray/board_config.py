"""Adafruit JD79661 2.13" 4-gray E-Ink — CircuitPython"""

import board
from displayio import release_displays
from fourwire import FourWire
from jd79661 import JD79661

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

_epaper = JD79661(
    display_bus,
    width=128,
    height=250,
    busy_pin=board.D7,
    rotation=0,
)

display_drv = EPaperDisplay(_epaper, width=128, height=250, color_depth=2)

broker = eventsys.Broker()
broker.register_quit_cleanup(display_drv)
