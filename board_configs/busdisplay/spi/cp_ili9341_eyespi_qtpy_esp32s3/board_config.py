"""CircuitPython variant — see paired MicroPython config in sibling directory."""

import board
from displayio import release_displays
from fourwire import FourWire
from st7789 import ST7789

import eventsys

release_displays()

display_bus = FourWire(
    board.SPI(),
    command=board.TX,
    chip_select=board.RX,
    baudrate=40_000_000,
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
)
from adafruit_focaltouch import Adafruit_FocalTouch

i2c = board.I2C()
touch_drv = Adafruit_FocalTouch(i2c)


def touch_read_func():
    touches = touch_drv.touches
    if len(touches):
        return touches[0]["x"], touches[0]["y"]
    return None


touch_rotation_table = (6, 3, 0, 5)

broker = eventsys.Broker()
touch_dev = broker.create(
    type=eventsys.TOUCH,
    read=touch_read_func,
    data=display_drv,
    data2=touch_rotation_table,
)

broker.register_quit_cleanup(display_drv)
