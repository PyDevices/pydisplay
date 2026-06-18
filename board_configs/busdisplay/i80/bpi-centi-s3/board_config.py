"""BPI-Centi-S3 170x320 ST7789 display"""

from i80bus import I80Bus
from machine import Pin
from rotary_irq_esp import RotaryIRQ
from st7789 import ST7789

from eventsys import devices

display_rd_pin = Pin(7, Pin.OUT, value=1)

display_bus = I80Bus(
    dc=5,
    cs=4,
    wr=6,
    data=[8, 9, 10, 11, 12, 13, 14, 15],
)

display_drv = ST7789(
    display_bus,
    width=170,
    height=320,
    colstart=35,
    rowstart=0,
    rotation=0,
    mirrored=False,
    color_depth=16,
    bgr=False,
    reverse_bytes_in_word=True,
    invert=True,
    brightness=1.0,
    backlight_pin=2,
    backlight_on_high=True,
    reset_pin=3,
    reset_high=True,
    power_pin=None,
    power_on_high=True,
)

encoder_drv = RotaryIRQ(37, 47, pull_up=True, half_step=True)
encoder_read_func = encoder_drv.value
encoder_button = Pin(35, Pin.IN, Pin.PULL_UP)


def encoder_button_func():
    return not encoder_button.value()


broker = devices.Broker()

encoder_dev = broker.create_device(
    type=devices.types.ENCODER,
    read=encoder_read_func,
    read2=encoder_button_func,
)
