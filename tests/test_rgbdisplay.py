# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Tests for ``displaysys.rgbdisplay.RGBDisplay``."""

import unittest

import _env  # noqa: F401
from displaysys.rgbdisplay import RGBDisplay


class _FakePanel:
    def __init__(self):
        self.calls = []

    def present(self, x, y, w, h, buf):
        self.calls.append(("present", x, y, w, h, bytes(buf)))

    def backlight_on(self):
        self.calls.append(("backlight_on",))


class TestRGBDisplay(unittest.TestCase):
    def test_show_uses_present(self):
        panel = _FakePanel()
        d = RGBDisplay(panel, width=4, height=2, color_depth=16)
        d.fill_rect(0, 0, 4, 1, 0xF800)
        d.show()
        self.assertEqual(len(panel.calls), 1)
        self.assertEqual(panel.calls[0][0], "present")
        self.assertEqual(panel.calls[0][3], 4)
        self.assertEqual(panel.calls[0][4], 2)

    def test_show_falls_back_to_bitmap(self):
        class LegacyPanel:
            def __init__(self):
                self.calls = []

            def bitmap(self, x, y, w, h, buf):
                self.calls.append((x, y, w, h, len(buf)))

        panel = LegacyPanel()
        d = RGBDisplay(panel, width=2, height=2, color_depth=16)
        d.show()
        self.assertEqual(panel.calls[0][2:], (2, 2, 8))

    def test_init_turns_backlight_on(self):
        panel = _FakePanel()
        d = RGBDisplay(panel, width=2, height=2, color_depth=16)
        d.init()
        self.assertIn(("backlight_on",), panel.calls)


if __name__ == "__main__":
    unittest.main()
