# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Tests for ``epaperdisplay_chip`` sequence parsing."""

import unittest

from epaperdisplay_chip import _send_command_sequence


class _RecordingBus:
    def __init__(self):
        self.calls = []

    def send(self, command, data=None):
        self.calls.append((command, data or b""))


class TestEpaperChipSequence(unittest.TestCase):
    def test_two_byte_length_soft_reset_delay(self):
        bus = _RecordingBus()
        _send_command_sequence(bus, b"\x12\x80\x00\x14", two_byte_sequence_length=True)
        self.assertEqual(bus.calls[0][0], 0x12)
        self.assertEqual(bus.calls[0][1], b"")

    def test_refresh_command_single_byte(self):
        bus = _RecordingBus()
        _send_command_sequence(bus, b"\x20\x00")
        self.assertEqual(bus.calls, [(0x20, b"")])


if __name__ == "__main__":
    unittest.main()
