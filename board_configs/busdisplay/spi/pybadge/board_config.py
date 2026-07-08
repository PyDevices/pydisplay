"""Adafruit PyBadge LC ST7789 + shift-register buttons — MicroPython (SAMD51)"""

from keypad_shift import PYBADGE_BUTTON_MAP, ShiftRegisterButtons
from machine import Pin
from spibus import SPIBus
from st7789 import ST7789

import eventsys

display_bus = SPIBus(
    id=0,
    baudrate=24_000_000,
    sck=45,
    mosi=47,
    miso=46,
    dc=37,
    cs=39,
    reset=0,
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
    cp={
        "width": 320,
        "height": 240,
        "colstart": 0,
        "rowstart": 0,
        "rotation": 0,
        "mirrored": False,
        "color_depth": 16,
        "bgr": False,
        "reverse_bytes_in_word": True,
    },
)
buttons = ShiftRegisterButtons(
    clock=63,
    latch=32,
    data=62,
    mapping=PYBADGE_BUTTON_MAP,
)


runtime = eventsys.Runtime(display=display_drv)
runtime.add_keypad(read=buttons.read)
