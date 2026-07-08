"""SPD1656 1.54" 6-color ACeP — MicroPython (Feather SPI pinout)"""

from machine import SPI, Pin
from spd1656 import SPD1656
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
_epaper = SPD1656(
    display_bus,
    width=152,
    height=152,
    busy_pin=Pin(7, Pin.IN),
    rotation=0,
)

display_drv = EPaperDisplay(_epaper, width=152, height=152, color_depth=4)

runtime = None
