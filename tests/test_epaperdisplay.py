# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Tests for ``displaysys.epaperdisplay.EPaperDisplay``."""

import unittest
from unittest import mock

import _env  # noqa: F401
from displaysys.epaperdisplay import EPaperDisplay


class _FakeEpaper:
    width = 8
    height = 8
    black_bits_inverted = False
    refresh_count = 0

    def refresh(self):
        self.refresh_count += 1


class _FakeBus:
    def __init__(self):
        self.calls = []

    def send(self, command, data=None):
        self.calls.append((command, data))


class _FakeEpaperWithBus(_FakeEpaper):
    write_black_ram_command = 0x24
    write_color_ram_command = 0x26
    set_column_window_command = 0x2A
    set_row_window_command = 0x2B
    set_current_column_command = 0x4E
    set_current_row_command = 0x4F
    colstart = 0
    rowstart = 0
    address_little_endian = False
    color_bits_inverted = False

    def __init__(self):
        self.bus = _FakeBus()


class TestEPaperDisplayDrawing(unittest.TestCase):
    def test_auto_allocates_1bpp_buffer(self):
        ep = _FakeEpaper()
        d = EPaperDisplay(ep, width=8, height=8, color_depth=1)
        self.assertEqual(len(d._buffer), 8)

    def test_fill_rect_1bpp_sets_bits(self):
        ep = _FakeEpaper()
        d = EPaperDisplay(ep, width=8, height=8, color_depth=1)
        d.fill_rect(0, 0, 8, 1, 1)
        self.assertEqual(d._buffer[0], 0xFF)

    def test_show_calls_refresh(self):
        ep = _FakeEpaper()
        d = EPaperDisplay(ep, width=8, height=8, color_depth=1)
        d.show()
        self.assertEqual(ep.refresh_count, 1)

    def test_show_pushes_buffer_over_bus(self):
        ep = _FakeEpaperWithBus()
        d = EPaperDisplay(ep, width=8, height=8, color_depth=1)
        d.fill_rect(0, 0, 8, 1, 1)
        with mock.patch(
            "displaysys.epaperdisplay.EPaperDisplay._push_buffer_displayio",
            side_effect=ImportError,
        ):
            d.show()
        self.assertTrue(any(call[0] == 0x24 for call in ep.bus.calls))
        self.assertEqual(ep.refresh_count, 1)

    def test_auto_allocates_4bpp_buffer(self):
        ep = _FakeEpaper()
        d = EPaperDisplay(ep, width=8, height=8, color_depth=4)
        self.assertEqual(len(d._buffer), 32)

    def test_fill_rect_4bpp_packs_nibbles(self):
        ep = _FakeEpaper()
        d = EPaperDisplay(ep, width=4, height=2, color_depth=4)
        d.fill_rect(0, 0, 4, 2, 0x0A)
        self.assertEqual(d._buffer[0], 0xAA)
        self.assertEqual(d._buffer[1], 0xAA)
        self.assertEqual(d._buffer[2], 0xAA)
        self.assertEqual(d._buffer[3], 0xAA)

    def test_show_pushes_tri_color_planes(self):
        ep = _FakeEpaperWithBus()
        d = EPaperDisplay(ep, width=4, height=1, color_depth=2)
        d.fill_rect(0, 0, 1, 1, 1)
        d.fill_rect(1, 0, 1, 1, 2)
        with mock.patch(
            "displaysys.epaperdisplay.EPaperDisplay._push_buffer_displayio",
            side_effect=ImportError,
        ):
            d.show()
        ram_cmds = [call[0] for call in ep.bus.calls if call[1] is not None]
        self.assertIn(0x24, ram_cmds)
        self.assertIn(0x26, ram_cmds)


if __name__ == "__main__":
    unittest.main()
