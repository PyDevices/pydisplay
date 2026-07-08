"""IL91874 2.7" tri-color shield — MicroPython (Feather SPI pinout)"""

from il91874 import IL91874
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
_epaper = IL91874(
    display_bus,
    width=264,
    height=176,
    busy_pin=Pin(7, Pin.IN),
    rotation=0,
    highlight_color=True,
)

display_drv = EPaperDisplay(_epaper, width=264, height=176, color_depth=2)

runtime = None
