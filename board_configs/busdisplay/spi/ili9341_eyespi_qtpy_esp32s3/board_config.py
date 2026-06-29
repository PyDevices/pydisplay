"""QTPy ESP32S3 with EyeSPI and ILI9341 2.8" display"""

from ft6x36 import FT6x36
from ili9341 import ILI9341
from machine import I2C, Pin
from spibus import SPIBus

from add_ons.quit_handler import wire_display_quit
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
    backlight_pin=None,
    backlight_on_high=True,
    reset_pin=None,
    reset_high=True,
    power_pin=None,
    power_on_high=True,
)

i2c = I2C(0, sda=Pin(7), scl=Pin(6), freq=100000)
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

wire_display_quit(broker)
