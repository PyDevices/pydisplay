# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Tests for ``tt21100.TT21100``."""

import struct
import sys
import types
import unittest
from unittest import mock

import _env  # noqa: F401


def _patch_time():
    time_mod = types.ModuleType("time")

    def ticks_ms():
        return 0

    def ticks_add(a, b):
        return a + b

    def ticks_diff(a, b):
        return a - b

    def sleep_ms(_ms):
        return None

    time_mod.ticks_ms = ticks_ms
    time_mod.ticks_add = ticks_add
    time_mod.ticks_diff = ticks_diff
    time_mod.sleep_ms = sleep_ms
    return mock.patch.dict(sys.modules, {"time": time_mod})


def _touch_packet(x, y, touch_id=0, pressure=32):
    """Build a 17-byte TT21100 touch report (7-byte header + 10-byte point)."""
    header = bytes([0x07, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00])
    point = struct.pack("xBHHBxxx", touch_id, x, y, pressure)
    return header + point


class _FakeI2C:
    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = []

    def readfrom(self, address, length, buf):
        self.calls.append((address, length))
        if not self._responses:
            raise AssertionError("unexpected readfrom")
        data = self._responses.pop(0)
        if isinstance(data, tuple):
            data = bytes(data)
        buf[:length] = data[:length]


class TestTT21100(unittest.TestCase):
    def test_init_waits_for_clear(self):
        i2c = _FakeI2C([bytes([1, 0]), bytes([0, 0])])
        with _patch_time():
            from tt21100 import TT21100

            TT21100(i2c, address=0x24)

    def test_touches_empty_when_no_data(self):
        i2c = _FakeI2C([bytes([0, 0]), bytes([0, 0])])
        with _patch_time():
            from tt21100 import TT21100

            touch = TT21100(i2c)
            self.assertEqual(touch.touches, [])

    def test_touches_header_only_packet(self):
        i2c = _FakeI2C([bytes([0, 0]), bytes([7, 0]), b"\x00" * 7])
        with _patch_time():
            from tt21100 import TT21100

            touch = TT21100(i2c)
            self.assertEqual(touch.touches, [])

    def test_touches_parses_single_point(self):
        packet = _touch_packet(120, 80, touch_id=3, pressure=40)
        i2c = _FakeI2C(
            [bytes([0, 0]), bytes([len(packet) & 0xFF, len(packet) >> 8]), packet]
        )
        with _patch_time():
            from tt21100 import TT21100

            touch = TT21100(i2c)
            points = touch.touches
            self.assertEqual(len(points), 1)
            self.assertEqual(points[0]["x"], 120)
            self.assertEqual(points[0]["y"], 80)
            self.assertEqual(points[0]["id"], 3)
            self.assertEqual(points[0]["pressure"], 40)


if __name__ == "__main__":
    unittest.main()
