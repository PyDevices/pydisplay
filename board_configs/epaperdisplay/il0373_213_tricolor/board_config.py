"""IL0373 2.13" tri-color FeatherWing — MicroPython (Feather SPI pinout)"""

from machine import Pin, SPI
from il0373 import IL0373
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

_epaper = IL0373(
    display_bus,
    width=250,
    height=122,
    busy_pin=Pin(7, Pin.IN),
    rotation=0,
    highlight_color=True,
)

display_drv = EPaperDisplay(_epaper, width=250, height=122, color_depth=2)

broker = eventsys.Broker()
broker.register_quit_cleanup(display_drv)
