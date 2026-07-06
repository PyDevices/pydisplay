"""Adafruit IL91874 2.7" tri-color shield — CircuitPython"""

import board
from displayio import release_displays
from fourwire import FourWire
from il91874 import IL91874

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

_epaper = IL91874(
    display_bus,
    width=264,
    height=176,
    busy_pin=board.D7,
    rotation=0,
    highlight_color=True,
)

display_drv = EPaperDisplay(_epaper, width=264, height=176, color_depth=2)

broker = eventsys.Broker()
broker.register_quit_cleanup(display_drv)
