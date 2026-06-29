"""
RPi Pico with ILI9341 2.8" TFT Touch Shield for Arduino with Capacitive Touch V2
Using Raspberry Pi Pico to Uno FlexyPin Adapter:
    https://www.digikey.com/en/products/detail/pimoroni-ltd/SP033/17051434
See ICSP Jumpers at:
    https://learn.adafruit.com/adafruit-2-8-tft-touch-shield-v2/tsc2007-pinouts
"""

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
)

i2c = I2C(0, sda=Pin(20), scl=Pin(21), freq=100000)
touch_drv = FT6x36(i2c)
touch_read_func = touch_drv.get_positions
touch_rotation_table = (6, 3, 0, 5)

broker = eventsys.Broker()

touch_dev = broker.create(
    type=eventsys.TOUCH,
    read=touch_read_func,
    data=display_drv,
    data2=touch_rotation_table,
)

broker.register_quit_cleanup(display_drv)
