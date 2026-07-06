"""SSD1677 5.83" monochrome bare display — MicroPython (Feather SPI pinout)"""

from machine import Pin, SPI
from ssd1677 import SSD1677
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

_epaper = SSD1677(
    display_bus,
    width=648,
    height=480,
    busy_pin=Pin(7, Pin.IN),
    rotation=0,
)

display_drv = EPaperDisplay(_epaper, width=648, height=480, color_depth=1)

broker = eventsys.Broker()
broker.register_quit_cleanup(display_drv)
