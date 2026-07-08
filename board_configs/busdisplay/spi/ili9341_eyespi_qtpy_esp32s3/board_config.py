"""QTPy ESP32S3 with EyeSPI and ILI9341 2.8" display"""

from ft6x36 import FT6x36
from ili9341 import ILI9341
from machine import I2C, Pin
from spibus import SPIBus

import eventsys

display_bus = SPIBus(
    id=1,
    baudrate=40_000_000,
    sck=36,
    mosi=35,
    miso=37,
    dc=16,
    cs=5,
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
    backlight_on_high=True,
    reset_high=True,
    power_on_high=True,
    cp={
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
i2c = I2C(0, sda=Pin(7), scl=Pin(6), freq=100_000)
touch_drv = FT6x36(i2c)
touch_read_func = touch_drv.get_positions
touch_rotation_table = (6, 3, 0, 5)

runtime = eventsys.Runtime(
    display=display_drv,
    touch_read=touch_read_func,
    touch_rotation_table=touch_rotation_table,
)
