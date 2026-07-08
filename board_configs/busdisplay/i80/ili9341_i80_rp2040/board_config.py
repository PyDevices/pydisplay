"""DIY Raspberry Pi Pico with ILI9341 2.8" display"""

from ft6x36 import FT6x36
from i80bus import I80Bus
from ili9341 import ILI9341
from machine import I2C, Pin

import eventsys

reset = Pin(12, Pin.OUT, value=1)
display_bus = I80Bus(
    dc=14,
    cs=15,
    wr=13,
    data=[0, 1, 2, 3, 4, 5, 6, 7],
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
    reset_pin=None,
    reset_high=True,
    power_pin=None,
    power_on_high=True,
)
i2c = I2C(0, sda=Pin(16), scl=Pin(17), freq=100_000)
touch_drv = FT6x36(i2c)
touch_read_func = touch_drv.get_positions
touch_rotation_table = None

runtime = eventsys.Runtime(
    display=display_drv,
    touch_read=touch_read_func,
    touch_rotation_table=touch_rotation_table,
)
