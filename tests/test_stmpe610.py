# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Tests for ``stmpe610.STMPE610``."""

import sys
import types
import unittest
from unittest import mock

import _env  # noqa: F401


class _FakePin:
    OUT = 1
    IN = 0

    def __init__(self, *_args, **_kwargs):
        self._value = 1

    def __call__(self, value=None):
        if value is not None:
            self._value = value
        return self._value

    def init(self, *_args, **_kwargs):
        return None


class TestSTMPE610(unittest.TestCase):
    def _make_touch(self):
        machine = types.ModuleType("machine")
        machine.Pin = _FakePin
        with mock.patch.dict(sys.modules, {"machine": machine}):
            from stmpe610 import STMPE610

            touch = STMPE610.__new__(STMPE610)
            touch._width = 240
            touch._height = 320
            touch._rotation = 0
            touch._calib = ((0, 4095), (0, 4095))
            touch._write_byte = lambda *_args, **_kwargs: None
            return touch

    def test_not_touched_returns_none(self):
        touch = self._make_touch()
        type(touch).touched = property(lambda self: False)
        self.assertIsNone(touch.touch_point)

    def test_touch_point_uses_calibration(self):
        touch = self._make_touch()
        touch._calib = ((357, 3812), (390, 3555))
        type(touch).touched = property(lambda self: True)
        type(touch).buffer_empty = property(lambda self: True)
        touch._read_raw = lambda: (2048, 2048, 128)
        point = touch.touch_point
        self.assertIsNotNone(point)


if __name__ == "__main__":
    unittest.main()
