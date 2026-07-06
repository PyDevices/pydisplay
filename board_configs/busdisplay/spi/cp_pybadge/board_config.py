"""Adafruit PyBadge LC ST7789 320x240 — CircuitPython"""

import board
from displayio import release_displays
from fourwire import FourWire
from keypad_gpio import GPIOButtons, MAGTAG_BUTTON_KEYS
from st7789 import ST7789

import eventsys

release_displays()

display_bus = FourWire(
    board.SPI(),
    command=board.TFT_DC,
    chip_select=board.TFT_CS,
    reset=board.TFT_RESET,
    baudrate=24_000_000,
)

display_drv = ST7789(
    display_bus,
    width=320,
    height=240,
    colstart=0,
    rowstart=0,
    rotation=0,
    mirrored=False,
    color_depth=16,
    bgr=False,
    reverse_bytes_in_word=True,
)

buttons = GPIOButtons(
    {
        "a": (board.BUTTON_A, MAGTAG_BUTTON_KEYS[0]),
        "b": (board.BUTTON_B, MAGTAG_BUTTON_KEYS[1]),
        "c": (board.BUTTON_C, MAGTAG_BUTTON_KEYS[2]),
        "d": (board.BUTTON_D, MAGTAG_BUTTON_KEYS[3]),
    }
)

broker = eventsys.Broker()

keypad_dev = broker.create(
    type=eventsys.KEYPAD,
    read=buttons.read,
)

broker.register_quit_cleanup(display_drv)
