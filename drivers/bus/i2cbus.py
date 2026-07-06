# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT

"""
i2cbus — I2C display bus for SSD1306-class OLED panels (MicroPython).

Implements the ``send(command, data)`` contract used by ``BusDisplay``.
"""

from micropython import const

_CO_DATA = const(0x40)
_CO_CMD = const(0x00)


class I2CBus:
    """
    I2C bus for displayio-style OLED controllers.

    Args:
        i2c: ``machine.I2C`` instance.
        address (int): I2C device address (default 0x3C).
    """

    def __init__(self, i2c, address=0x3C):
        self._i2c = i2c
        self._address = address

    def send(self, command, data=None):
        if data is None:
            data = b""
        if isinstance(command, int):
            self._i2c.writeto(self._address, bytes([_CO_CMD, command]) + bytes(data))
        else:
            self._i2c.writeto(self._address, bytes([_CO_CMD]) + bytes(command) + bytes(data))

    def send_data(self, data):
        self._i2c.writeto(self._address, bytes([_CO_DATA]) + bytes(data))
