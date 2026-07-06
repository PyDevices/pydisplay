"""CircuitPython variant — see paired MicroPython config in sibling directory."""

import board
from displayio import release_displays
from fourwire import FourWire
from cst226 import CST226

import eventsys

release_displays()

display_bus = FourWire(
    board.SPI(),
    command=board.D10,
    chip_select=board.D9,
    baudrate=40_000_000,
)

display_drv = CST226(
    display_bus,
    width=240,
    height=320,
    rotation=0,
    color_depth=16,
    bgr=False,
    reverse_bytes_in_word=True,
)

broker = eventsys.Broker()

broker.register_quit_cleanup(display_drv)
