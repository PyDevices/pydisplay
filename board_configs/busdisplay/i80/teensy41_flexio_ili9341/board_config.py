"""Teensy 4.1 + external ILI9341 on FlexIO 8080 bus — MicroPython

Wires an 8-bit parallel ILI9341 to **MIMXRT1062 FlexIO2** pads (displayif ``i80bus``).
Data must be eight **consecutive** FlexIO2 indices on ``GPIO_B0_xx`` / ``GPIO_B1_xx``.

Example mapping (external breakout — **do not** use MIMXRT1060-EVK RK043 RGB pins):

| Signal | Teensy / MP pin name |
|--------|----------------------|
| D0-D7  | ``GPIO_B1_00`` ... ``GPIO_B1_07`` (FlexIO2 D16-D23) |
| WR     | ``GPIO_B1_08`` (FlexIO2 D24) |
| DC     | ``GPIO_B1_09`` |
| CS     | ``GPIO_B1_10`` |

Requires displayif ``i80bus`` (FlexIO MCULCD) on mimxrt1062 firmware.

CircuitPython sibling: none (use ``paralleldisplaybus`` on a CP board with I80).
"""

from ili9341 import ILI9341
from machine import Pin

import eventsys

try:
    from i80bus import I80Bus
except ImportError as exc:
    raise NotImplementedError(
        "FlexIO 8080 bus requires displayif i80bus cmod (mimxrt1062 port)"
    ) from exc

_DATA = tuple(Pin(f"GPIO_B1_{i:02d}") for i in range(8))

display_bus = I80Bus(
    dc=Pin("GPIO_B1_09"),
    cs=Pin("GPIO_B1_10"),
    wr=Pin("GPIO_B1_08"),
    data=_DATA,
    freq=20_000_000,
)

display_drv = ILI9341(
    display_bus,
    width=240,
    height=320,
    colstart=0,
    rowstart=0,
    rotation=0,
    mirrored=False,
    color_depth=16,
    bgr=True,
    reverse_bytes_in_word=True,
    invert=False,
    brightness=1.0,
    backlight_pin=None,
    backlight_on_high=True,
    reset_pin=Pin("GPIO_B1_11"),
    reset_high=True,
    power_pin=None,
    power_on_high=True,
)

runtime = None
