"""DIY ESP32 psram with and ILI9341 2.8" display and XPT2046 touch controller"""

from ili9341 import ILI9341
from machine import SPI, Pin
from spibus import SPIBus
from xpt2046 import Touch

from add_ons.quit_handler import wire_display_quit
import eventsys

display_bus = SPIBus(
    id=1,
    baudrate=40_000_000,
    sck=14,
    mosi=13,
    miso=12,
    dc=5,
    cs=15,
)

display_drv = ILI9341(
    display_bus,
    width=240,
    height=320,
    colstart=0,
    rowstart=0,
    rotation=270,
    mirrored=False,
    color_depth=16,
    bgr=True,
    reverse_bytes_in_word=True,
    invert=False,
    brightness=1.0,
    backlight_pin=None,
    backlight_on_high=True,
    reset_pin=4,
    reset_high=False,
    power_pin=22,
    power_on_high=True,
)

spi = SPI(2, baudrate=1000000, sck=Pin(18), mosi=Pin(23), miso=Pin(19))
touch_drv = Touch(
    spi=spi,
    cs=Pin(25),
    int_pin=Pin(21),
)

# Display rotation 270 degrees, invert Y axis 0b100
touch_drv.calibrate(
    xmin=107,
    xmax=2000,
    ymin=200,
    ymax=1940,
    width=display_drv.height,
    height=display_drv.width,
    orientation=3,
)

touch_read_func = (touch_drv.get_touch,)
touch_rotation_table = (0b000, 0b000, 0b000, 0b100)

broker = eventsys.Broker()

touch_dev = broker.create(
    type=eventsys.TOUCH,
    read=touch_read_func,
    data=display_drv,
    data2=touch_rotation_table,
)

wire_display_quit(broker)
