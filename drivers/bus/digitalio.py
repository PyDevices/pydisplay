# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT

"""
digitalio — MicroPython shim for vendored CircuitPython e-paper drivers.
"""

from machine import Pin

OUTPUT = Pin.OUT
INPUT = Pin.IN


class Direction:
    OUTPUT = Pin.OUT
    INPUT = Pin.IN


class Pull:
    UP = Pin.PULL_UP
    DOWN = Pin.PULL_DOWN


class DigitalInOut:
    def __init__(self, pin):
        if hasattr(pin, "value"):
            self._pin = pin
        else:
            self._pin = Pin(pin, Pin.OUT)

    @property
    def direction(self):
        return self._direction

    @direction.setter
    def direction(self, value):
        self._direction = value
        if value == Direction.OUTPUT:
            self._pin.init(Pin.OUT)
        else:
            self._pin.init(Pin.IN)

    @property
    def value(self):
        return self._pin.value()

    @value.setter
    def value(self, val):
        self._pin.value(val)

    def switch_to_input(self, pull=None):
        kwargs = {}
        if pull is not None:
            kwargs["pull"] = pull
        self._pin.init(Pin.IN, **kwargs)

    def deinit(self):
        return
