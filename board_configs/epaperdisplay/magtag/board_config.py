"""Adafruit MagTag SSD1680 E-Ink — MicroPython"""

from keypad_gpio import MAGTAG_BUTTON_KEYS, GPIOButtons
from machine import Pin
from spibus import SPIBus
from ssd1680 import SSD1680

from displaysys.epaperdisplay import EPaperDisplay
import eventsys

display_bus = SPIBus(
    id=1,
    baudrate=4_000_000,
    sck=36,
    mosi=35,
    miso=37,
    dc=7,
    cs=8,
    reset=6,
)

_epaper = SSD1680(
    display_bus,
    width=296,
    height=128,
    busy_pin=Pin(5, Pin.IN),
    rotation=0,
)

display_drv = EPaperDisplay(_epaper, width=296, height=128, color_depth=1)

buttons = GPIOButtons(
    {
        "a": (Pin(15, Pin.IN, Pin.PULL_UP), MAGTAG_BUTTON_KEYS[0]),
        "b": (Pin(14, Pin.IN, Pin.PULL_UP), MAGTAG_BUTTON_KEYS[1]),
        "c": (Pin(12, Pin.IN, Pin.PULL_UP), MAGTAG_BUTTON_KEYS[2]),
        "d": (Pin(11, Pin.IN, Pin.PULL_UP), MAGTAG_BUTTON_KEYS[3]),
    }
)

runtime = eventsys.Runtime(display=display_drv)
runtime.add_keypad(read=buttons.read)
