# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Tests for ``i2cbus.I2CBus``."""

import unittest

import _env  # noqa: F401


class _FakeI2C:
    def __init__(self):
        self.writes = []

    def writeto(self, address, buf):
        self.writes.append((address, bytes(buf)))


class TestI2CBus(unittest.TestCase):
    def test_send_command_only(self):
        from i2cbus import I2CBus

        i2c = _FakeI2C()
        bus = I2CBus(i2c, address=0x3C)
        bus.send(0xAF)
        self.assertEqual(i2c.writes, [(0x3C, bytes([0x00, 0xAF]))])

    def test_send_command_with_data(self):
        from i2cbus import I2CBus

        i2c = _FakeI2C()
        bus = I2CBus(i2c)
        bus.send(0x21, b"\x01\x02")
        self.assertEqual(i2c.writes[0][1], bytes([0x00, 0x21, 0x01, 0x02]))

    def test_send_data(self):
        from i2cbus import I2CBus

        i2c = _FakeI2C()
        bus = I2CBus(i2c)
        bus.send_data(b"\xAA\xBB")
        self.assertEqual(i2c.writes[0][1], bytes([0x40, 0xAA, 0xBB]))


if __name__ == "__main__":
    unittest.main()
