# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT

"""74HC165 shift-register keypad helper for PyBadge / PyGamer."""

from machine import Pin

try:
    from eventsys.keys import Keys
except ImportError:
    from keys import Keys


class ShiftRegisterButtons:
    """
    Read buttons wired to a 74HC165 shift register.

    Args:
        clock: Clock pin.
        latch: Latch pin.
        data: Serial data out pin.
        mapping: Dict of name -> (bit_index, key_code).
        key_count (int): Number of bits to clock out.
        value_when_pressed (bool): Raw bit value when pressed.
    """

    def __init__(
        self,
        clock,
        latch,
        data,
        mapping,
        *,
        key_count=8,
        value_when_pressed=True,
    ):
        self._clock = Pin(clock, Pin.OUT)
        self._latch = Pin(latch, Pin.OUT)
        self._data = Pin(data, Pin.IN, Pin.PULL_UP)
        self._key_count = key_count
        self._value_when_pressed = value_when_pressed
        self._buttons = [(bit_index, key_code) for bit_index, key_code in mapping.values()]

    def _read_bits(self):
        self._latch.value(0)
        self._latch.value(1)
        self._latch.value(0)
        bits = []
        for _ in range(self._key_count):
            bits.append(self._data.value())
            self._clock.value(1)
            self._clock.value(0)
        return bits

    def read(self):
        bits = self._read_bits()
        pressed = []
        for bit_index, key in self._buttons:
            if bits[bit_index] == self._value_when_pressed:
                pressed.append(key)
        return pressed


PYBADGE_BUTTON_MAP = {
    "a": (1, Keys.K_a),
    "b": (0, Keys.K_b),
    "c": (2, Keys.K_c),
    "d": (3, Keys.K_d),
}
