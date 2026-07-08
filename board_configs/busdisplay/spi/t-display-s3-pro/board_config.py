"""T-Display-S3 Pro 222x480 ST7796 display"""

from cst226 import CST226
from machine import I2C, Pin
from spibus import SPIBus
from st7796 import ST7796

import eventsys

display_bus = SPIBus(
    id=1,
    baudrate=60_000_000,
    sck=18,
    mosi=17,
    miso=8,
    dc=9,
    cs=39,
)

display_drv = ST7796(
    display_bus,
    width=222,
    height=480,
    colstart=49,
    rowstart=0,
    rotation=0,
    mirrored=False,
    color_depth=16,
    bgr=True,
    reverse_bytes_in_word=True,
    invert=True,
    brightness=1.0,
    backlight_pin=48,
    backlight_on_high=True,
    reset_pin=47,
    reset_high=False,
    power_pin=None,
    power_on_high=True,
    cp={
        "width": 222,
        "height": 480,
        "colstart": 49,
        "rowstart": 0,
        "rotation": 0,
        "mirrored": False,
        "color_depth": 16,
        "bgr": True,
        "reverse_bytes_in_word": True,
        "invert": True,
        "brightness": 1.0,
        "backlight_pin": "board.GP48",
        "backlight_on_high": True,
        "reset_high": False,
    },
)
i2c = I2C(0, sda=Pin(5), scl=Pin(6), freq=100_000)
touch_drv = CST226(i2c, irq_pin=21, rst_pin=13)
touch_read_func = touch_drv.get_point
touch_rotation_table = (0, 5, 6, 3)

runtime = eventsys.Runtime(
    display=display_drv,
    touch_read=touch_read_func,
    touch_rotation_table=touch_rotation_table,
)
