"""SSD1680 2.13\" E-Ink FeatherWing — MicroPython (Feather RP2040 / M4 pinout)"""

from machine import Pin, SPI
from spibus import SPIBus
from ssd1680 import SSD1680

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

_epaper = SSD1680(
    display_bus,
    width=250,
    height=122,
    busy_pin=Pin(7, Pin.IN),
    rotation=0,
)

display_drv = EPaperDisplay(_epaper, width=250, height=122, color_depth=1)

broker = eventsys.Broker()
broker.register_quit_cleanup(display_drv)
