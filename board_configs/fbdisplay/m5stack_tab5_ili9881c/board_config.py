"""M5Stack Tab5 (ILI9881C + GT911) - MicroPython"""

import time

from gt911 import GT911
from machine import I2C, Pin
from pi4ioe5v import tab5_init_lcd_reset
from tab5_ili9881c_init import TAB5_ILI9881C_INIT

from displaysys.fbdisplay import FBDisplay
import eventsys

try:
    from mipidsi import Bus, Display
except ImportError as exc:
    raise NotImplementedError("MIPI DSI requires displayif mipidsi cmod (esp32p4 port)") from exc

I2C_SCL = 32
I2C_SDA = 31
LCD_BACKLIGHT = 22
TOUCH_INT = 23

i2c = I2C(0, scl=Pin(I2C_SCL), sda=Pin(I2C_SDA), freq=400_000)
tab5_init_lcd_reset(i2c)
time.sleep_ms(100)

touch_drv = GT911(
    i2c,
    reset_pin=None,
    irq_pin=TOUCH_INT,
    address=0x14,
    width=720,
    height=1_280,
    touch_points=5,
)

bus = Bus(frequency=730_000_000, num_lanes=2)

fb = Display(
    bus,
    init_sequence=TAB5_ILI9881C_INIT,
    width=720,
    height=1_280,
    color_depth=16,
    pixel_clock_frequency=60_000_000,
    hsync_pulse_width=40,
    hsync_front_porch=40,
    hsync_back_porch=140,
    vsync_pulse_width=4,
    vsync_front_porch=20,
    vsync_back_porch=20,
    backlight_pin=LCD_BACKLIGHT,
    backlight_on_high=True,
)


def touch_read_func():
    n, points = touch_drv.read_points()
    if n:
        return points[0][0], points[0][1]
    return None


touch_rotation_table = (0, 0, 0, 0)

display_drv = FBDisplay(fb)

runtime = eventsys.Runtime(
    display=display_drv,
    touch_read=touch_read_func,
    touch_rotation_table=touch_rotation_table,
)
