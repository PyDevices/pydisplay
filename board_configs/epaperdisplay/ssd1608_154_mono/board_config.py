"""SSD1608 1.54" monochrome breakout — MicroPython (Feather SPI pinout)"""

from machine import Pin, SPI
from ssd1608 import SSD1608
from spibus import SPIBus

from displaysys.epaperdisplay import EPaperDisplay
import eventsys

display_bus = SPIBus(
    id=0,
    baudrate=4_000_000,
    sck=18,
    mosi=19,
    miso=-1,
    dc=9,
    cs=10,
    reset=6,
)

_epaper = SSD1608(
    display_bus,
    width=200,
    height=200,
    busy_pin=Pin(7, Pin.IN),
    rotation=0,
)

display_drv = EPaperDisplay(_epaper, width=200, height=200, color_depth=1)

broker = eventsys.Broker()
broker.register_quit_cleanup(display_drv)
