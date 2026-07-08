"""7.3" ACeP 7-color E-Ink — MicroPython (Feather SPI pinout)"""

from acep7in import ACeP7In
from machine import SPI, Pin
from spibus import SPIBus

from displaysys.epaperdisplay import EPaperDisplay
import eventsys

display_bus = SPIBus(
    id=0,
    baudrate=24_000_000,
    sck=18,
    mosi=19,
    miso=-1,
    dc=10,
    cs=9,
    reset=6,
)
_epaper = ACeP7In(
    display_bus,
    width=800,
    height=480,
    rotation=0,
)

display_drv = EPaperDisplay(_epaper, width=800, height=480, color_depth=4)

runtime = None
