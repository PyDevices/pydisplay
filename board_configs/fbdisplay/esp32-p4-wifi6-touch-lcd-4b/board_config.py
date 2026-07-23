"""Waveshare ESP32-P4-WIFI6-Touch-LCD-4B - MicroPython"""

import time

from gt911 import GT911
from machine import I2C, Pin

from displaysys.fbdisplay import FBDisplay
import eventsys

try:
    from mipidsi import Bus, Display
except ImportError as exc:
    raise NotImplementedError("MIPI DSI requires displayif mipidsi cmod (esp32p4 port)") from exc

LCD_RESET = 27
LCD_BACKLIGHT = 26
I2C_SCL = 8
I2C_SDA = 7
TOUCH_RESET = 23
TOUCH_IRQ_DUMMY = 22

ST7703_INIT_SEQUENCE = (
    b"\xb9\x03\xf1\x12\x83"
    b"\xb1\x05\x00\x00\x00\xda\x80"
    b"\xb2\x03\x3c\x12\x30"
    b"\xb3\x0a\x10\x10\x28\x28\x03\xff\x00\x00\x00\x00"
    b"\xb4\x01\x80"
    b"\xb5\x02\x0a\x0a"
    b"\xb6\x02\x97\x97"
    b"\xb8\x04\x26\x22\xf0\x13"
    b"\xba\x1b\x31\x81\x0f\xf9\x0e\x06\x20\x00\x00\x00\x00\x00\x00\x00\x44\x25\x00\x90\x0a\x00\x00\x01\x4f\x01\x00\x00\x37"
    b"\xbc\x01\x47"
    b"\xbf\x03\x02\x11\x00"
    b"\xc0\x09\x73\x73\x50\x50\x00\x00\x12\x70\x00"
    b"\xc1\x0c\x25\x00\x32\x32\x77\xe4\xff\xff\xcc\xcc\x77\x77"
    b"\xc6\x06\x82\x00\xbf\xff\x00\xff"
    b"\xc7\x06\xb8\x00\x0a\x10\x01\x09"
    b"\xc8\x04\x10\x40\x1e\x02"
    b"\xcc\x01\x0b"
    b"\xe0\x22\x00\x0b\x10\x2c\x3d\x3f\x42\x3a\x07\x0d\x0f\x13\x15\x13\x14\x0f\x16\x00\x0b\x10\x2c\x3d\x3f\x42\x3a\x07\x0d\x0f\x13\x15\x13\x14\x0f\x16"
    b"\xe3\x0e\x07\x07\x0b\x0b\x0b\x0b\x00\x00\x00\x00\xff\x00\xc0\x10"
    b"\xe9\x3f\xc8\x10\x0a\x00\x00\x80\x81\x12\x31\x23\x4f\x86\xa0\x00\x47\x08\x00\x00\x0c\x00\x00\x00\x00\x00\x0c\x00\x00\x00\x98\x02\x8b\xaf\x46\x02\x88\x88\x88\x88\x88\x98\x13\x8b\xaf\x57\x13\x88\x88\x88\x88\x88\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\xea\x3d\x97\x0c\x09\x09\x09\x78\x00\x00\x00\x00\x00\x00\x9f\x31\x8b\xa8\x31\x75\x88\x88\x88\x88\x88\x9f\x20\x8b\xa8\x20\x64\x88\x88\x88\x88\x88\x23\x00\x00\x02\x71\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x40\x80\x81\x00\x00\x00\x00"
    b"\xef\x03\xff\xff\x01"
    b"\x11\x81\x00\xfa"
    b"\x29\x81\x00\x32"
)

lcd_reset = Pin(LCD_RESET, Pin.OUT, value=1)
lcd_reset.value(0)
time.sleep_ms(100)
lcd_reset.value(1)
time.sleep_ms(200)

bus = Bus(frequency=1_000_000_000, num_lanes=2, ldo_chan=3, ldo_voltage_mv=2500)

fb = Display(
    bus,
    init_sequence=ST7703_INIT_SEQUENCE,
    width=720,
    height=720,
    color_depth=16,
    pixel_clock_frequency=46_000_000,
    hsync_pulse_width=20,
    hsync_front_porch=80,
    hsync_back_porch=80,
    vsync_pulse_width=4,
    vsync_front_porch=30,
    vsync_back_porch=12,
    reset_pin=LCD_RESET,
    backlight_pin=LCD_BACKLIGHT,
    backlight_on_high=False,
)
i2c = I2C(1, scl=Pin(I2C_SCL), sda=Pin(I2C_SDA), freq=400_000)

touch_drv = GT911(
    i2c,
    reset_pin=TOUCH_RESET,
    irq_pin=TOUCH_IRQ_DUMMY,
    address=0x5D,
    width=720,
    height=720,
    touch_points=5,
    reverse_axis=False,
    # Factory Y already matches the FB; X is mirrored (left→high). reverse_* are
    # applied in software by gt911 when update_config is False (default).
    reverse_x=True,
    reverse_y=False,
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
