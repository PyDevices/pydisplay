# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Tests for ``graphics`` text rendering (``Font`` and the ``text*`` helpers)."""

import unittest

import _env  # noqa: F401
from _support import count_set, make_fb

from graphics import Area, Font, text, text8, text14, text16


class TestFontObject(unittest.TestCase):
    def test_default_font_is_8x8(self):
        f = Font(height=8)
        self.assertEqual(f.width, 8)
        self.assertEqual(f.height, 8)

    def test_text_width_scales(self):
        f = Font(height=8)
        self.assertEqual(f.text_width("AB"), 16)
        self.assertEqual(f.text_width("AB", scale=2), 32)

    def test_memoryview_font_data(self):
        # 256 chars * 8 rows == 2048 bytes -> height 8.
        data = memoryview(bytearray(256 * 8))
        f = Font(data, 8)
        self.assertEqual(f.height, 8)
        self.assertEqual(f.font_name, "memoryview")


class TestTextHelpers(unittest.TestCase):
    def setUp(self):
        self.fb = make_fb(w=64, h=32)
        self.fb.fill(0)

    def test_text8_returns_area(self):
        self.assertEqual(text8(self.fb, "Hi", 0, 0, 0xFFFF), Area(0, 0, 16, 8))

    def test_text14_returns_area(self):
        self.assertEqual(text14(self.fb, "Hi", 0, 0, 0xFFFF), Area(0, 0, 16, 14))

    def test_text16_returns_area(self):
        self.assertEqual(text16(self.fb, "Hi", 0, 0, 0xFFFF), Area(0, 0, 16, 16))

    def test_text_actually_draws_pixels(self):
        text8(self.fb, "A", 0, 0, 0xFFFF)
        self.assertGreater(count_set(self.fb), 0)

    def test_text_blank_string_draws_nothing(self):
        text8(self.fb, " ", 0, 0, 0xFFFF)
        self.assertEqual(count_set(self.fb), 0)

    def test_newline_advances_a_row(self):
        bbox = text8(self.fb, "A\nB", 0, 0, 0xFFFF)
        # two lines of an 8px-high font
        self.assertEqual(bbox.h, 16)


class TestTextSelector(unittest.TestCase):
    def setUp(self):
        self.fb = make_fb(w=64, h=32)
        self.fb.fill(0)

    def test_height_dispatch(self):
        self.assertEqual(text(self.fb, "X", 0, 0, 0xFFFF, height=8).h, 8)
        self.assertEqual(text(self.fb, "X", 0, 0, 0xFFFF, height=14).h, 14)
        self.assertEqual(text(self.fb, "X", 0, 0, 0xFFFF, height=16).h, 16)

    def test_unsupported_height_raises(self):
        with self.assertRaises(ValueError):
            text(self.fb, "X", 0, 0, 0xFFFF, height=13)


if __name__ == "__main__":
    unittest.main()
