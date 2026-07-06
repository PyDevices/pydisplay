"""Adafruit PiTFT 2.4\" FeatherWing ILI9341 + STMPE610 — MicroPython (Feather)"""

from machine import Pin, SPI
from ili9341 import ILI9341
from spibus import SPIBus
from stmpe610 import STMPE610

import eventsys

display_bus = SPIBus(
    id=0,
    baudrate=24_000_000,
    sck=18,
    mosi=19,
    miso=20,
    dc=10,
    cs=9,
    reset=6,
)

display_drv = ILI9341(
    display_bus,
    width=240,
    height=320,
    colstart=0,
    rowstart=0,
    rotation=90,
    mirrored=False,
    color_depth=16,
    bgr=True,
    reverse_bytes_in_word=True,
)

touch_spi = SPI(0, baudrate=1_000_000, sck=Pin(18), mosi=Pin(19), miso=Pin(20))
touch_drv = STMPE610(touch_spi, cs=8, width=240, height=320, rotation=90)


def touch_read_func():
    if touch_drv.touched:
        point = touch_drv.touch_point
        if point is not None:
            return point
    return None


touch_rotation_table = (0, 0, 0, 0)

broker = eventsys.Broker()

touch_dev = broker.create(
    type=eventsys.TOUCH,
    read=touch_read_func,
    data=display_drv,
    data2=touch_rotation_table,
)

broker.register_quit_cleanup(display_drv)
