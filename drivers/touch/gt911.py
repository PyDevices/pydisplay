"""
This file is part of the OpenMV project.

Copyright (c) 2023 Ibrahim Abdelkader <iabdalkader@openmv.io>
Copyright (c) 2023 Kwabena W. Agyeman <kwagyeman@openmv.io>

This work is licensed under the MIT license, see the file LICENSE for details.

GT911 5-Point Capacitive Touch Controller driver for MicroPython.

Basic polling mode example usage:

import time
from gt911 import GT911
from machine import I2C

# Note use pin numbers or names not Pin objects because the
# driver needs to change pin directions to reset the controller.
touch = GT911(I2C(1, freq=400_000), reset_pin="P1", irq_pin="P2", touch_points=5)

while True:
    n, points = touch.read_points()
    for i in range(0, n):
        print(f"id {points[i][3]} x {points[i][0]} y {points[i][1]} size {points[i][2]}")
    time.sleep_ms(100)
"""

from array import array
from time import sleep_ms

from machine import Pin
from micropython import const

# OpenMV uses Pin.OUT_PP; standard MicroPython / CircuitPython ports use Pin.OUT.
_PIN_OUT = getattr(Pin, "OUT_PP", Pin.OUT)

_DEFAULT_ADDR = const(0x5D)

_COMMAND = const(0x8040)
_REFRESH_RATE = const(0x8056)
_RESOLUTION_X = const(0x8048)
_RESOLUTION_Y = const(0x804A)
_TOUCH_POINTS = const(0x804C)
_MODULE_SWITCH1 = const(0x804D)
_CONFIG_CHKSUM = const(0x80FF)
_CONFIG_FRESH = const(0x8100)
# First touch point follows the status byte at 0x814E (Espressif esp_lcd_touch_gt911).
_POINT_DATA_START = const(0x814F)
_DATA_BUFFER = const(0x814E)


def _as_out_pin(pin, *, value=0):
    """``machine.Pin`` from an id, or an existing pin-like (e.g. IO-expander)."""
    if isinstance(pin, (int, str)):
        return Pin(pin, _PIN_OUT, value=value)
    # Expander / duck-typed pins: drive initial level, keep the object.
    if value is not None:
        try:
            pin(value)
        except TypeError:
            pin.value(value)
    return pin


class GT911:
    def __init__(
        self,
        bus,
        reset_pin,
        irq_pin,
        address=_DEFAULT_ADDR,
        width=800,
        height=480,
        touch_points=1,
        reverse_x=False,
        reverse_y=False,
        reverse_axis=True,
        sito=True,
        refresh_rate=240,
        touch_callback=None,
        update_config=False,
    ):
        self.bus = bus
        self.address = address
        self.touch_callback = touch_callback
        self.rst_pin = _as_out_pin(reset_pin, value=0)
        self.irq_pin = None
        self.irq_pin_label = irq_pin
        self.width = int(width)
        self.height = int(height)
        self.reverse_x = bool(reverse_x)
        self.reverse_y = bool(reverse_y)
        self.reverse_axis = bool(reverse_axis)
        # Chip config rewrite is optional; without it, apply axis flags in software
        # on each read so reverse_* always match the constructor contract.
        self._hw_axis_config = bool(update_config)

        # Reset the touch panel controller.
        self.reset()

        # Optional: rewrite firmware config. Many panels (e.g. Waveshare GT911)
        # ship a working factory config — rewriting it can stop touch reports.
        if update_config:
            self._write_reg(_RESOLUTION_X, width, 2)
            self._write_reg(_RESOLUTION_Y, height, 2)
            self._write_reg(_TOUCH_POINTS, touch_points)
            self._write_reg(
                _MODULE_SWITCH1,
                (int(reverse_y) << 7)
                | (int(reverse_x) << 6)
                | (int(reverse_axis) << 3)
                | (int(sito) << 2)
                | 0x01,
            )
            self._write_reg(_REFRESH_RATE, (1000 * 1000) // (refresh_rate * 250))
            self._write_reg(_COMMAND, 0x00)
            self._update_config()

        # Allocate scratch buffer: x, y, size, track_id
        self.points_data = [array("H", [0, 0, 0, 0]) for x in range(5)]

    def _read_reg(self, reg, size=1, buf=None):
        if buf is not None:
            self.bus.readfrom_mem_into(self.address, reg, buf, addrsize=16)
        else:
            return self.bus.readfrom_mem(self.address, reg, size, addrsize=16)

    def _write_reg(self, reg, val, size=1):
        buf = bytes([val & 0xFF]) if size == 1 else bytes([val & 0xFF, val >> 8])
        self.bus.writeto_mem(self.address, reg, buf, addrsize=16)

    def _update_config(self):
        # Read current config
        chksum = ~sum(self._read_reg(0x8047, 184)) + 1
        # Calculate checksum
        self._write_reg(_CONFIG_CHKSUM, chksum)
        # Update the config
        self._write_reg(_CONFIG_FRESH, 0x01)

    def read_id(self):
        return self._read_reg(0x8140, 4)

    def read_points(self):
        """Return ``(n, points)`` only when the GT911 buffer-ready bit is set.

        Matching Espressif ``esp_lcd_touch_gt911``: ignore the point-count
        nibble unless bit 0x80 is set. Returning a stale nibble without a fresh
        buffer read re-reports old ``points_data`` (often 0,0) and pins the
        cursor at the top-left.
        """
        status = self._read_reg(_DATA_BUFFER)[0]
        if not (status & 0x80):
            return 0, self.points_data
        n_points = status & 0x0F
        if n_points == 0 or n_points > 5:
            self._write_reg(_DATA_BUFFER, 0)
            return 0, self.points_data
        # One contiguous read: status is at 0x814E; points follow at 0x814F.
        buf = self._read_reg(_POINT_DATA_START, n_points * 8)
        for i in range(n_points):
            o = i * 8
            # Packed: track_id, x_lo, x_hi, y_lo, y_hi, size_lo, size_hi, reserved
            x = buf[o + 1] | (buf[o + 2] << 8)
            y = buf[o + 3] | (buf[o + 4] << 8)
            size = buf[o + 5] | (buf[o + 6] << 8)
            if not self._hw_axis_config:
                if self.reverse_axis:
                    x, y = y, x
                if self.reverse_x:
                    x = self.width - 1 - x
                if self.reverse_y:
                    y = self.height - 1 - y
            self.points_data[i][0] = x
            self.points_data[i][1] = y
            self.points_data[i][2] = size
            self.points_data[i][3] = buf[o]
        self._write_reg(_DATA_BUFFER, 0)
        return n_points, self.points_data

    def reset(self):
        if self.irq_pin is not None:
            self.irq_pin.irq(handler=None)
        self.rst_pin(0)
        sleep_ms(10)
        self.irq_pin = Pin(self.irq_pin_label, _PIN_OUT, value=0)
        sleep_ms(50)
        self.rst_pin(1)
        # Note must wait for at least 50ms before switching the IRQ pin to input.
        sleep_ms(100)
        self.irq_pin = Pin(self.irq_pin_label, Pin.IN, Pin.PULL_UP)
        if self.touch_callback is not None:
            self.irq_pin.irq(handler=self.touch_callback, trigger=Pin.IRQ_FALLING, hard=False)
