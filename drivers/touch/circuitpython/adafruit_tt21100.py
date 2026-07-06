# SPDX-FileCopyrightText: 2017 Scott Shawcroft, written for Adafruit Industries
# SPDX-FileCopyrightText: Copyright (c) 2022 Scott Shawcroft for Adafruit Industries
#
# SPDX-License-Identifier: MIT
"""
`adafruit_tt21100`
================================================================================

Basic driver for TT21100 touchscreen drivers


* Author(s): Scott Shawcroft

Implementation Notes
--------------------

**Hardware:**

* `Espressif ESP32-S3 Box <https://www.adafruit.com/product/5290>`_

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://circuitpython.org/downloads
* Adafruit's Bus Device library: https://github.com/adafruit/Adafruit_CircuitPython_BusDevice

"""




import array
import struct
import time

from adafruit_bus_device.i2c_device import I2CDevice

try:
    from typing import List
except ImportError:
    pass

# This is based on:
# https://github.com/espressif/esp-box/blob/master/components/i2c_devices/touch_panel/tt21100.c


class TT21100:
    """
    A driver for the TT21100 capacitive touch sensor.
    """

    def __init__(self, i2c, address=0x24, irq_pin=None):
        self._i2c = I2CDevice(i2c, address)
        self._irq_pin = irq_pin

        self._bytes = bytearray(28)
        self._data_len = array.array("H", [0])

        # Poll for start up.
        with self._i2c as i2c_transaction:
            while self._data_len[0] != 0x0000:
                i2c_transaction.readinto(self._data_len)
                time.sleep(0.02)

    @property
    def touched(self) -> int:
        """Returns the number of touches currently detected"""
        with self._i2c as i2c:
            i2c.readinto(self._data_len)
            # Throw away packets that are header only because they don't actually
            # have any touches
            if self._data_len[0] == 7:
                i2c.readinto(self._bytes, end=7)

        if self._data_len[0] % 10 == 7:
            return self._data_len[0] // 10
        return 0

    @property
    def touches(self) -> List[dict]:
        """
        Returns a list of touchpoint dicts, with 'x' and 'y' containing the
        touch coordinates, and 'id' as the touch # for multitouch tracking
        """
        touchpoints = []
        self._bytes[2] = 0
        while self._bytes[2] != 1:
            with self._i2c as i2c:
                i2c.readinto(self._data_len)
                # Empty queue
                if self._data_len[0] in {0, 2}:
                    return []
                i2c.readinto(self._bytes, end=self._data_len[0])

        for i in range(self._data_len[0] // 10):
            touch_id, x, y, pressure = struct.unpack_from(
                "xBHHBxxx", self._bytes, offset=10 * i + 7
            )
            touch_id &= 0x1F
            point = {"x": x, "y": y, "id": touch_id, "pressure": pressure}

            touchpoints.append(point)
        return touchpoints
