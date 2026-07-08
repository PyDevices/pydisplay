"""EK79686 2.7" tri-color breakout — MicroPython (Feather SPI pinout)"""

from ek79686 import EK79686
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
_epaper = EK79686(
    display_bus,
    width=176,
    height=264,
    busy_pin=Pin(7, Pin.IN),
    rotation=0,
    highlight_color=True,
)

display_drv = EPaperDisplay(_epaper, width=176, height=264, color_depth=2)

runtime = None
