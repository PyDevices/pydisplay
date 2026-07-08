"""RPi Pico with ILI9341 2.8" TFT Touch Shield"""

from ft6x36 import FT6x36
from ili9341 import ILI9341
from machine import I2C, Pin
from spibus import SPIBus

import eventsys

display_bus = SPIBus(
    id=0,
    baudrate=62_500_000,
    sck=18,
    mosi=19,
    miso=16,
    dc=3,
    cs=17,
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
    cp={
        "width": 240,
        "height": 320,
        "colstart": 0,
        "rowstart": 0,
        "rotation": 0,
        "mirrored": False,
        "color_depth": 16,
        "bgr": True,
        "reverse_bytes_in_word": True,
        "invert": False,
    },
)
i2c = I2C(0, sda=Pin(20), scl=Pin(21), freq=100_000)
touch_drv = FT6x36(i2c)
touch_read_func = touch_drv.get_positions
touch_rotation_table = (6, 3, 0, 5)

runtime = eventsys.Runtime(
    display=display_drv,
    touch_read=touch_read_func,
    touch_rotation_table=touch_rotation_table,
)
