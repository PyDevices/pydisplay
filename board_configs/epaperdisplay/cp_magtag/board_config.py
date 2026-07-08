"""Adafruit MagTag 2.9\" grayscale E-Ink (SSD1680) — CircuitPython"""

import board
from displayio import release_displays
from fourwire import FourWire
from keypad_gpio import MAGTAG_BUTTON_KEYS, GPIOButtons
from ssd1680 import SSD1680

from displaysys.epaperdisplay import EPaperDisplay
import eventsys

release_displays()

display_bus = FourWire(
    board.SPI(),
    command=board.EPD_DC,
    chip_select=board.EPD_CS,
    reset=board.EPD_RESET,
    baudrate=4_000_000,
)

_epaper = SSD1680(
    display_bus,
    width=296,
    height=128,
    busy_pin=board.EPD_BUSY,
    rotation=0,
    ram_offset=1,
)

display_drv = EPaperDisplay(_epaper, width=296, height=128, color_depth=1)

buttons = GPIOButtons(
    {
        "a": (board.BUTTON_A, MAGTAG_BUTTON_KEYS[0]),
        "b": (board.BUTTON_B, MAGTAG_BUTTON_KEYS[1]),
        "c": (board.BUTTON_C, MAGTAG_BUTTON_KEYS[2]),
        "d": (board.BUTTON_D, MAGTAG_BUTTON_KEYS[3]),
    }
)

runtime = eventsys.Runtime(display=display_drv)
runtime.add_keypad(read=buttons.read)
