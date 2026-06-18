"""T-Display-S3 Pro 222x480 ST7796 display - contributed by @tdhoward
https://github.com/Xinyuan-LilyGO/T-Display-S3-Pro/blob/master/schematic/T-Display-Pro.pdf
"""

from cst226 import CST226
from machine import I2C, Pin
from spibus import SPIBus
from st7796 import ST7796

from eventsys import devices

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
)


i2c = I2C(0, sda=Pin(5), scl=Pin(6), freq=100000)
touch_drv = CST226(i2c, irq_pin=21, rst_pin=13)
touch_read_func = touch_drv.get_point
# Set to (0,0,0,0), reset and run pydisplay_touch_test.py if touch rotation is wrong
touch_rotation_table = (0, 5, 6, 3)

broker = devices.Broker()

touch_dev = broker.create_device(
    type=devices.types.TOUCH,
    read=touch_read_func,
    data=display_drv,
    data2=touch_rotation_table,
)
