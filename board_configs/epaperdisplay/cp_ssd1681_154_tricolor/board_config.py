"""Adafruit SSD1681 1.54" tri-color breakout — CircuitPython"""

import board
from displayio import release_displays
from fourwire import FourWire
from ssd1681 import SSD1681

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

_epaper = SSD1681(
    display_bus,
    width=200,
    height=200,
    busy_pin=board.D7,
    rotation=0,
    highlight_color=True,
)

display_drv = EPaperDisplay(_epaper, width=200, height=200, color_depth=2)

broker = eventsys.Broker()
broker.register_quit_cleanup(display_drv)
