# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Tests for ``graphics.FrameBuffer`` (the ``_framebuf_plus`` wrapper).

This is the ``FrameBuffer`` exported from the package. Unlike the bare
``framebuf`` base class, every drawing method returns an :class:`graphics.Area`
bounding box and the buffer/format/color_depth are exposed as properties.
"""

import unittest

import _env  # noqa: F401
from _support import make_fb

import graphics
from graphics import (
    GS2_HMSB,
    GS4_HMSB,
    GS8,
    MONO_HLSB,
    MONO_HMSB,
    MONO_VLSB,
    RGB565,
    Area,
    FrameBuffer,
)

_DEPTHS = {
    MONO_VLSB: 1,
    MONO_HLSB: 1,
    MONO_HMSB: 1,
    RGB565: 16,
    GS2_HMSB: 2,
    GS4_HMSB: 4,
    GS8: 8,
}


class TestProperties(unittest.TestCase):
    def test_dimensions_and_format(self):
        buffer = bytearray(20 * 10 * 2)
        fb = FrameBuffer(buffer, 20, 10, RGB565)
        self.assertEqual(fb.width, 20)
        self.assertEqual(fb.height, 10)
        self.assertEqual(fb.format, RGB565)
        self.assertIs(fb.buffer, buffer)

    def test_color_depth_for_each_format(self):
        for fmt, depth in _DEPTHS.items():
            with self.subTest(format=fmt):
                fb = make_fb(fmt, 8, 8)
                self.assertEqual(fb.color_depth, depth)

    def test_invalid_format_raises(self):
        with self.assertRaises(ValueError):
            FrameBuffer(bytearray(64), 4, 4, 99)


class TestMethodsReturnArea(unittest.TestCase):
    def setUp(self):
        self.fb = make_fb(RGB565, 16, 16)

    def test_fill_returns_area(self):
        self.assertEqual(self.fb.fill(0), Area(0, 0, 16, 16))

    def test_fill_rect_returns_area(self):
        self.assertEqual(self.fb.fill_rect(2, 3, 4, 5, 0xFFFF), Area(2, 3, 4, 5))

    def test_pixel_set_returns_area(self):
        self.assertEqual(self.fb.pixel(1, 1, 0xFFFF), Area(1, 1, 1, 1))

    def test_pixel_get_returns_int(self):
        self.fb.pixel(1, 1, 0x1234)
        self.assertEqual(self.fb.pixel(1, 1), 0x1234)

    def test_hline_returns_area(self):
        self.assertEqual(self.fb.hline(0, 0, 5, 0xFFFF), Area(0, 0, 5, 1))

    def test_vline_returns_area(self):
        self.assertEqual(self.fb.vline(0, 0, 5, 0xFFFF), Area(0, 0, 1, 5))

    def test_rect_returns_area(self):
        self.assertEqual(self.fb.rect(1, 1, 5, 6, 0xFFFF), Area(1, 1, 5, 6))

    def test_line_returns_area(self):
        self.assertIsInstance(self.fb.line(0, 0, 5, 5, 0xFFFF), Area)

    def test_ellipse_returns_area(self):
        self.assertEqual(self.fb.ellipse(8, 8, 3, 2, 0xFFFF), Area(5, 6, 6, 4))

    def test_blit_returns_area(self):
        src = make_fb(RGB565, 4, 4)
        src.fill(0xABCD)
        self.assertEqual(self.fb.blit(src, 2, 2), Area(2, 2, 4, 4))
        self.assertEqual(self.fb.pixel(2, 2), 0xABCD)


class TestDrawingEffects(unittest.TestCase):
    def setUp(self):
        self.fb = make_fb(RGB565, 16, 16)
        self.fb.fill(0)

    def test_fill_rect_sets_interior_only(self):
        self.fb.fill_rect(4, 4, 3, 3, 0xFFFF)
        self.assertEqual(self.fb.pixel(4, 4), 0xFFFF)
        self.assertEqual(self.fb.pixel(6, 6), 0xFFFF)
        self.assertEqual(self.fb.pixel(7, 7), 0)

    def test_rect_outline_is_hollow(self):
        self.fb.rect(2, 2, 6, 6, 0xFFFF)
        # corners drawn, centre untouched
        self.assertEqual(self.fb.pixel(2, 2), 0xFFFF)
        self.assertEqual(self.fb.pixel(7, 7), 0xFFFF)
        self.assertEqual(self.fb.pixel(4, 4), 0)

    def test_rect_filled(self):
        self.fb.rect(2, 2, 6, 6, 0xFFFF, True)
        self.assertEqual(self.fb.pixel(4, 4), 0xFFFF)


if __name__ == "__main__":
    unittest.main()
