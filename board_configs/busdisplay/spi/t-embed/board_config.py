"""T-Embed ST7789 display with encoder"""

from machine import Pin
from rotary_irq_esp import RotaryIRQ
from spibus import SPIBus
from st7789 import ST7789

from eventsys import devices

display_bus = SPIBus(
    id=1,
    baudrate=60_000_000,
    sck=12,
    mosi=11,
    miso=-1,
    dc=13,
    cs=10,
)

display_drv = ST7789(
    display_bus,
    width=170,
    height=320,
    colstart=0,
    rowstart=0,
    rotation=0,
    mirrored=False,
    color_depth=16,
    bgr=False,
    reverse_bytes_in_word=True,
    invert=False,
    brightness=1.0,
    backlight_pin=15,
    backlight_on_high=True,
    reset_pin=None,
    reset_high=True,
    power_pin=None,
    power_on_high=True,
)

encoder_drv = RotaryIRQ(1, 2, pull_up=True, half_step=True)
encoder_read_func = encoder_drv.value
encoder_button = Pin(0, Pin.IN, Pin.PULL_UP)


def encoder_button_func():
    return not encoder_button.value()


broker = devices.Broker()

encoder_dev = broker.create_device(
    type=devices.types.ENCODER,
    read=encoder_read_func,
    read2=encoder_button_func,
)
