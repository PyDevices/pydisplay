"""Waveshare ESP32-S3-Touch-LCD-7 — 800x480 RGB565 (ST7262) + GT911

Pin map / timings match ESP32_Display_Panel / Waveshare wiki for
``ESP32-S3-Touch-LCD-7`` (same RGB GPIO map as the 4.3″ sibling).
Backlight + LCD/touch reset via CH422G on I2C (SDA=8, SCL=9).
"""

import time

from ch422g import CH422G
from gt911 import GT911
from machine import I2C, Pin

from displaysys.fbdisplay import FBDisplay
import eventsys

try:
    import displayif
except ImportError as exc:
    raise NotImplementedError(
        "Parallel RGB scanout requires displayif.DotClockFramebuffer (esp32 port)"
    ) from exc

# CH422G EXIO map (Waveshare wiki / ESP_PANEL backlight IO=2)
_TP_RST = 1
_LCD_BL = 2
_LCD_RST = 3
_TP_INT = 4

i2c = I2C(0, sda=Pin(8), scl=Pin(9), freq=400_000)
print(f"i2c.scan() = {i2c.scan()}")

iox = CH422G(i2c)
iox.enable_all_io_output()
iox.digital_write(_LCD_BL, 1)
# LCD reset
iox.digital_write(_LCD_RST, 0)
time.sleep_ms(10)
iox.digital_write(_LCD_RST, 1)
time.sleep_ms(100)

tft_pins = {
    "de": 5,
    "vsync": 3,
    "hsync": 46,
    "dclk": 7,
    # RGB565 D0..D15 (B0..B4, G0..G5, R0..R4)
    "data": (14, 38, 18, 17, 10, 39, 0, 45, 48, 47, 21, 1, 2, 42, 41, 40),
}

tft_timings = {
    "frequency": 16_000_000,
    "width": 800,
    "height": 480,
    "hsync_pulse_width": 4,
    "hsync_front_porch": 8,
    "hsync_back_porch": 8,
    "vsync_pulse_width": 4,
    "vsync_front_porch": 8,
    "vsync_back_porch": 8,
    "hsync_idle_low": False,
    "vsync_idle_low": False,
    "de_idle_high": False,
    "pclk_active_high": False,
    "pclk_idle_high": False,
}

fb = displayif.DotClockFramebuffer(**tft_pins, **tft_timings)
display_drv = FBDisplay(fb)

# GT911: RST on CH422G EXIO1, INT=GPIO4 (address-select during reset → 0x5D)
touch_drv = GT911(
    i2c,
    reset_pin=iox.Pin(_TP_RST, Pin.OUT, value=1),
    irq_pin=_TP_INT,
    address=0x5D,
    width=800,
    height=480,
    touch_points=5,
    reverse_axis=False,
)


def touch_read_func():
    """GT911 reports panel coords directly on the 7″ (unlike the 4.3″ diagonal map)."""
    n, points = touch_drv.read_points()
    if not n:
        return None
    return points[0][0], points[0][1]


touch_rotation_table = (0, 0, 0, 0)

runtime = eventsys.Runtime(
    display=display_drv,
    touch_read=touch_read_func,
    touch_rotation_table=touch_rotation_table,
)
