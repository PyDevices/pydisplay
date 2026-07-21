"""NXP MIMXRT1060-EVK + RK043FN66HS-CTG 4.3" parallel RGB - MicroPython"""

import time

from gt911 import GT911
from machine import I2C, Pin

from displaysys.fbdisplay import FBDisplay
import eventsys

try:
    import displayif
except ImportError as exc:
    raise NotImplementedError(
        "Parallel RGB scanout requires displayif.DotClockFramebuffer (mimxrt eLCDIF)"
    ) from exc

LCD_BACKLIGHT = Pin("GPIO_B1_15", Pin.OUT, value=1)
LCD_RESET = Pin("GPIO_AD_B0_02", Pin.OUT, value=1)

Pin("GPIO_AD_B0_02", Pin.OUT, value=1).value(0)
time.sleep_ms(10)
Pin("GPIO_AD_B0_02", Pin.OUT, value=1).value(1)
time.sleep_ms(120)

tft_pins = {
    "de": Pin("GPIO_B0_01"),
    "vsync": Pin("GPIO_B0_03"),
    "hsync": Pin("GPIO_B0_02"),
    "dclk": Pin("GPIO_B0_00"),
    "data": (
        Pin("GPIO_B0_04"),
        Pin("GPIO_B0_05"),
        Pin("GPIO_B0_06"),
        Pin("GPIO_B0_07"),
        Pin("GPIO_B0_08"),
        Pin("GPIO_B0_09"),
        Pin("GPIO_B0_10"),
        Pin("GPIO_B0_11"),
        Pin("GPIO_B0_12"),
        Pin("GPIO_B0_13"),
        Pin("GPIO_B0_14"),
        Pin("GPIO_B0_15"),
        Pin("GPIO_B1_00"),
        Pin("GPIO_B1_01"),
        Pin("GPIO_B1_02"),
        Pin("GPIO_B1_03"),
    ),
}

tft_timings = {
    "frequency": 9_000_000,
    "width": 480,
    "height": 272,
    "hsync_pulse_width": 41,
    "hsync_front_porch": 4,
    "hsync_back_porch": 8,
    "vsync_pulse_width": 10,
    "vsync_front_porch": 4,
    "vsync_back_porch": 2,
    "hsync_idle_low": True,
    "vsync_idle_low": True,
    "de_idle_high": False,
    "pclk_active_high": False,
    "pclk_idle_high": False,
}

fb = displayif.DotClockFramebuffer(**tft_pins, **tft_timings)

display_drv = FBDisplay(fb)

i2c = I2C(0, freq=400_000)
touch_drv = GT911(
    i2c, reset_pin="GPIO_AD_B0_02", irq_pin="GPIO_AD_B0_11", width=480, height=272, touch_points=5
)
touch_read_func = touch_drv.get_positions
touch_rotation_table = (0, 0, 0, 0)

runtime = eventsys.Runtime(
    display=display_drv,
    touch_read=touch_read_func,
    touch_rotation_table=touch_rotation_table,
)
