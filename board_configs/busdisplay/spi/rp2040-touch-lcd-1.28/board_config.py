"""Waveshare RP2040-Touch-LCD-1.28 GC9A01 240x240"""

from gc9a01 import GC9A01
from machine import I2C, Pin
from spibus import SPIBus

import eventsys

display_bus = SPIBus(
    id=1,
    # Match Waveshare demo / known-good cold-boot probe (60 MHz was flaky on power-on).
    baudrate=10_000_000,
    sck=10,
    mosi=11,
    dc=8,
    cs=9,
)

display_drv = GC9A01(
    display_bus,
    width=240,
    height=240,
    colstart=0,
    rowstart=0,
    rotation=0,
    mirrored=False,
    color_depth=16,
    bgr=True,
    reverse_bytes_in_word=True,
    invert=True,
    brightness=1.0,
    backlight_pin=25,
    backlight_on_high=True,
    reset_pin=13,
    reset_high=False,
    power_pin=None,
    power_on_high=True,
)

# Waveshare RP2040-LCD-1.28 demo uses MADCTL 0x98 (BusDisplay rotation=0 sets 0x48).
display_drv.send(0x36, bytes([0x98]))
# BusDisplay programs COLMOD 0x55 after init; GC9A01A needs 0x05 (also done in driver).
display_drv.send(0x3A, bytes([0x05]))

# Prefer sticky GPIO backlight. PWM stops on soft-reset and looks like a blank panel.
try:
    bl = display_drv._backlight_pin
    if bl is not None and hasattr(bl, "deinit"):
        bl.deinit()
except Exception:
    pass
_bl = Pin(25, Pin.OUT)
_bl.value(1)
display_drv._backlight_pin = _bl
display_drv._backlight_is_pwm = False

touch_drv = None
touch_read_func = None
touch_rotation_table = (0, 5, 6, 3)

try:
    # timeout=ms where supported — prevents indefinite hang if CST8xx NACK/stuck.
    try:
        i2c = I2C(1, sda=Pin(6), scl=Pin(7), freq=100_000, timeout=1000)
    except TypeError:
        i2c = I2C(1, sda=Pin(6), scl=Pin(7), freq=100_000)
    from cst8xx import CST8XX

    touch_drv = CST8XX(i2c, irq_pin=21, rst_pin=22)
    touch_read_func = touch_drv.get_point
except Exception:
    touch_drv = None
    touch_read_func = None

runtime = eventsys.Runtime(
    display=display_drv,
    touch_read=touch_read_func,
    touch_rotation_table=touch_rotation_table,
)
