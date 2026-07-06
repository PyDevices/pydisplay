"""Adafruit MagTag 2.9\" grayscale E-Ink (SSD1680) — CircuitPython"""

import board
from displayio import release_displays
from fourwire import FourWire
from ssd1680 import SSD1680

import eventsys

release_displays()

spi = board.SPI()
epd_cs = board.EPD_CS
epd_dc = board.EPD_DC
epd_reset = board.EPD_RESET
epd_busy = board.EPD_BUSY

display_bus = FourWire(
    spi,
    command=epd_dc,
    chip_select=epd_cs,
    reset=epd_reset,
    baudrate=4000000,
)

display_drv = SSD1680(
    display_bus,
    width=296,
    height=128,
    busy_pin=epd_busy,
    rotation=0,
    ram_offset=1,
)

broker = eventsys.Broker()
broker.register_quit_cleanup(display_drv)
