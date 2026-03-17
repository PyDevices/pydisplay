"""ESP32 WROVER E with ST7789 display, and joystick instead of touchscreen"""

from gpiojoystick import GPIOJoystick
from spibus import SPIBus
from st7789 import ST7789
from eventsys import devices
from machine import ADC, Pin

display_bus = SPIBus(
    id=1,
    sck=14,
    mosi=12,
    dc=13,
    cs=15,
)

display_drv = ST7789(
    display_bus,
    width=240,
    height=240,
    colstart=0,
    rowstart=0,
    rotation=0,
    mirrored=True,
    color_depth=16,
    bgr=True,
    reverse_bytes_in_word=True,
    invert=False,
    brightness=1.0,
    backlight_pin=None,
    backlight_on_high=True,
)

joystick_driver = GPIOJoystick(
    instance_id=1,
    axes=[
        ADC(Pin(39), atten=ADC.ATTN_11DB),
        ADC(Pin(36), atten=ADC.ATTN_11DB)
    ],
    buttons=[
        Pin(4, Pin.IN, Pin.PULL_UP),
        Pin(25, Pin.IN, Pin.PULL_UP),
        Pin(26, Pin.IN, Pin.PULL_UP)
    ],
)

broker = devices.Broker()

joystick_dev = broker.create_device(
    type=devices.types.JOYSTICK,
    joystick_driver=joystick_driver,
    emulate_digital=[(0,1)]
)