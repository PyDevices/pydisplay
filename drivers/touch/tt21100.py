# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT

"""MicroPython driver for TT21100 capacitive touch controllers."""

import struct
import time


class TT21100:
    """TT21100 touch controller on I2C."""

    def __init__(self, i2c, address=0x24):
        self._i2c = i2c
        self._address = address
        self._bytes = bytearray(28)
        self._data_len = bytearray(2)
        deadline = time.ticks_add(time.ticks_ms(), 500)
        while time.ticks_diff(deadline, time.ticks_ms()) > 0:
            self._i2c.readfrom(self._address, 2, self._data_len)
            if self._data_len[0] == 0 and self._data_len[1] == 0:
                break
            time.sleep_ms(20)

    @property
    def touches(self):
        self._i2c.readfrom(self._address, 2, self._data_len)
        length = self._data_len[0] | (self._data_len[1] << 8)
        if length in (0, 2):
            return []
        if length % 10 == 7:
            self._i2c.readfrom(self._address, 7, self._bytes)
            return []
        if length % 10 != 7:
            return []
        self._i2c.readfrom(self._address, length, self._bytes)
        points = []
        for i in range(length // 10):
            touch_id, x, y, pressure = struct.unpack_from("xBHHBxxx", self._bytes, 10 * i + 7)
            points.append(
                {
                    "x": x,
                    "y": y,
                    "id": touch_id & 0x1F,
                    "pressure": pressure,
                }
            )
        return points
