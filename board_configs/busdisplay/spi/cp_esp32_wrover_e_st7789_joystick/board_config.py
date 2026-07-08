"""ESP32 WROVER-E ST7789 with GPIO joystick — CircuitPython"""

import board
from displayio import release_displays
from fourwire import FourWire
from st7789 import ST7789

import eventsys

release_displays()

display_bus = FourWire(
    board.SPI(),
    command=board.D13,
    chip_select=board.D15,
    baudrate=40_000_000,
)

display_drv = ST7789(
    display_bus,
    width=240,
    height=240,
    colstart=0,
    rowstart=0,
    rotation=0,
    mirrored=True,
    color_depth=16,
    bgr=True,
    reverse_bytes_in_word=True,
    invert=False,
)

# Joystick wiring is board-specific; register KEYPAD/JOYSTICK when ported.
runtime = None
