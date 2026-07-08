"""JD79661 2.13" 4-gray E-Ink — MicroPython (Feather SPI pinout)"""

from jd79661 import JD79661
from machine import SPI, Pin
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
_epaper = JD79661(
    display_bus,
    width=128,
    height=250,
    busy_pin=Pin(7, Pin.IN),
    rotation=0,
)

display_drv = EPaperDisplay(_epaper, width=128, height=250, color_depth=2)

runtime = None
