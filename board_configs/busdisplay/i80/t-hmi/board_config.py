"""T-HMI 240x320 ST7789V display"""

from i80bus import I80Bus
from machine import SPI, Pin  # See the note about reset below
from st7789 import ST7789
from xpt2046 import Touch

from eventsys import devices

display_bus = I80Bus(
    dc=7,
    cs=6,
    wr=8,
    data=[48, 47, 39, 40, 41, 42, 45, 46],
)

display_drv = ST7789(
    display_bus,
    width=320,
    height=240,
    colstart=0,
    rowstart=0,
    rotation=0,
    mirrored=False,
    color_depth=16,
    bgr=False,
    reverse_bytes_in_word=False,
    invert=True,
    brightness=1.0,
    backlight_pin=38,
    backlight_on_high=True,
    reset_pin=None,
    reset_high=True,
    power_pin=None,
    power_on_high=True,
)

spi = SPI(1, baudrate=1000000)
touch_drv = Touch(
    spi=spi,
    cs=Pin(2),
    int_pin=Pin(9),
)

touch_drv.calibrate(
    xmin=150,
    xmax=1830,
    ymin=150,
    ymax=1830,
    width=display_drv.width,
    height=display_drv.height,
    orientation=1,
)

touch_read_func = touch_drv.get_touch
touch_rotation_table = None

broker = devices.Broker()

touch_dev = broker.create_device(
    type=devices.types.TOUCH,
    read=touch_read_func,
    data=display_drv,
    data2=touch_rotation_table,
)
