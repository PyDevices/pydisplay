"""UC8151D 2.9" flexible E-Ink breakout — MicroPython (Feather SPI pinout)"""

from machine import SPI, Pin
from spibus import SPIBus
from uc8151d import UC8151D

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
_epaper = UC8151D(
    display_bus,
    width=128,
    height=296,
    busy_pin=Pin(7, Pin.IN),
    rotation=0,
)

display_drv = EPaperDisplay(_epaper, width=128, height=296, color_depth=1)

runtime = None
