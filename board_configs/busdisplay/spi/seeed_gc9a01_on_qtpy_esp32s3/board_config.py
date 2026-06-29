"""Seeed Studio Round Display for XIAO GC9A01 240x240 display on Adafruit QT Py ESP32-S3"""

from chsc6x import CHSC6X
from gc9a01 import GC9A01
from machine import I2C, Pin
from spibus import SPIBus

from add_ons.quit_handler import wire_display_quit
import eventsys

display_bus = SPIBus(
    id=1,
    baudrate=60_000_000,
    sck=36,
    mosi=35,
    miso=37,
    dc=8,
    cs=17,
)

display_drv = GC9A01(
    display_bus,
    width=240,
    height=240,
    colstart=0,
    rowstart=0,
    rotation=0,
    mirrored=False,
    color_depth=16,
    bgr=True,
    reverse_bytes_in_word=True,
    invert=True,
    brightness=1.0,
    backlight_pin=None,
    backlight_on_high=True,
    reset_pin=None,
    reset_high=True,
    power_pin=None,
    power_on_high=True,
)

i2c = I2C(0, sda=Pin(7), scl=Pin(6), freq=400000)
touch_drv = CHSC6X(i2c, irq_pin=16)
touch_read_func = touch_drv.touch_read
touch_rotation_table = (0, 5, 6, 3)

broker = eventsys.Broker()

touch_dev = broker.create(
    type=eventsys.TOUCH,
    read=touch_read_func,
    data=display_drv,
    data2=touch_rotation_table,
)

wire_display_quit(broker)
