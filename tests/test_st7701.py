# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Tests for ``st7701.run_init``."""

import unittest
from unittest import mock

import _env  # noqa: F401


class _Pin:
    def __init__(self):
        self.values = []

    def __call__(self, val=None):
        if val is not None:
            self.values.append(val)
        return self.values[-1] if self.values else 0


class TestST7701Init(unittest.TestCase):
    def test_run_init_toggles_reset_and_cs(self):
        from st7701 import LCDPins, run_init

        pins = LCDPins(pwr_en=_Pin(), cs=_Pin(), sda=_Pin(), clk=_Pin(), rst=_Pin())
        with mock.patch("st7701.sleep_ms"):
            run_init(pins, init_sequence=[(0x11, b"\x00", 0)])
        self.assertIn(1, pins.rst.values)
        self.assertIn(0, pins.rst.values)
        self.assertTrue(any(v == 0 for v in pins.cs.values))


if __name__ == "__main__":
    unittest.main()
