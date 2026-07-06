# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Tests for ``keypad_shift.ShiftRegisterButtons``."""

import sys
import types
import unittest
from unittest import mock

import _env  # noqa: F401

try:
    from eventsys.keys import Keys
except ImportError:
    from keys import Keys


class _FakePin:
    IN = 0
    OUT = 1
    PULL_UP = 2

    def __init__(self, *_args, **_kwargs):
        pass

    def value(self, val=None):
        return 0

    def init(self, mode, pull=None):
        return None


class TestShiftRegisterButtons(unittest.TestCase):
  def test_read_uses_bit_mapping(self):
    machine = types.ModuleType("machine")
    machine.Pin = _FakePin
    with mock.patch.dict(sys.modules, {"machine": machine}):
      from keypad_shift import ShiftRegisterButtons

      buttons = ShiftRegisterButtons(
          clock=1,
          latch=2,
          data=3,
          mapping={"a": (0, Keys.K_a), "b": (1, Keys.K_b)},
          value_when_pressed=False,
      )
      buttons._read_bits = lambda: [0, 1, 1, 1, 1, 1, 1, 1]
      self.assertEqual(buttons.read(), [Keys.K_a])


if __name__ == "__main__":
  unittest.main()
