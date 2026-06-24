# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Tests for the pure-Python ``graphics._framebuf`` fallback FrameBuffer.

On MicroPython the native ``framebuf`` module is used instead, but on CPython
(and therefore in these tests) ``graphics`` falls back to this module, so it is
worth exercising directly. It returns plain tuples rather than ``Area``
objects; the ``graphics._framebuf_plus`` wrapper is what adds ``Area``.
"""

import unittest

import _env  # noqa: F401

from graphics._framebuf import (
    GS2_HMSB,
    GS4_HMSB,
    GS8,
    MONO_HLSB,
    MONO_VLSB,
    RGB565,
    FrameBuffer,
)

# Formats whose pure-Python get/set round-trip cleanly on CPython.
_ROUNDTRIP_FORMATS = (MONO_VLSB, MONO_HLSB, RGB565, GS2_HMSB)


def _fb(format, w=16, h=16):
    return FrameBuffer(bytearray(w * h * 2), w, h, format)


class TestFrameBufferBasics(unittest.TestCase):
    def test_invalid_format_raises(self):
        with self.assertRaises(ValueError):
            FrameBuffer(bytearray(16), 4, 4, 99)

    def test_width_height_properties(self):
        fb = _fb(RGB565, 12, 7)
        self.assertEqual(fb.width, 12)
        self.assertEqual(fb.height, 7)

    def test_pixel_set_returns_tuple_not_area(self):
        fb = _fb(RGB565)
        result = fb.pixel(1, 1, 0x1234)
        self.assertEqual(result, (1, 1, 1, 1))

    def test_pixel_out_of_bounds_returns_none(self):
        fb = _fb(RGB565, 8, 8)
        self.assertIsNone(fb.pixel(-1, 0))
        self.assertIsNone(fb.pixel(8, 0))
        self.assertIsNone(fb.pixel(0, 8))


class TestFrameBufferPixelRoundTrip(unittest.TestCase):
    def test_pixel_roundtrip(self):
        for fmt in _ROUNDTRIP_FORMATS:
            with self.subTest(format=fmt):
                fb = _fb(fmt)
                self.assertEqual(fb.pixel(3, 4), 0)
                fb.pixel(3, 4, 1)
                self.assertEqual(fb.pixel(3, 4), 1)
                # An untouched neighbour stays clear.
                self.assertEqual(fb.pixel(4, 4), 0)

    def test_rgb565_preserves_16bit_value(self):
        fb = _fb(RGB565)
        fb.pixel(2, 2, 0xBEEF)
        self.assertEqual(fb.pixel(2, 2), 0xBEEF)


class TestFrameBufferFill(unittest.TestCase):
    def test_fill_sets_every_pixel(self):
        fb = _fb(RGB565, 8, 8)
        fb.fill(0x07E0)
        self.assertTrue(all(fb.pixel(x, y) == 0x07E0 for x in range(8) for y in range(8)))

    def test_fill_returns_full_extent(self):
        fb = _fb(RGB565, 8, 8)
        self.assertEqual(fb.fill(0), (0, 0, 8, 8))

    def test_fill_rect_region(self):
        fb = _fb(RGB565, 8, 8)
        fb.fill(0)
        fb.fill_rect(2, 2, 3, 3, 0xFFFF)
        self.assertEqual(fb.pixel(2, 2), 0xFFFF)
        self.assertEqual(fb.pixel(4, 4), 0xFFFF)
        self.assertEqual(fb.pixel(5, 5), 0)
        self.assertEqual(fb.pixel(1, 1), 0)


class TestFrameBufferScroll(unittest.TestCase):
    def test_scroll_moves_pixels(self):
        fb = _fb(RGB565, 8, 8)
        fb.fill(0)
        fb.pixel(0, 0, 0xFFFF)
        fb.scroll(2, 3)
        self.assertEqual(fb.pixel(2, 3), 0xFFFF)

    def test_scroll_requires_byte_aligned_depth(self):
        fb = _fb(MONO_VLSB, 8, 8)
        with self.assertRaises(ValueError):
            fb.scroll(1, 1)


class TestUnimplementedFormats(unittest.TestCase):
    def test_gs4_pixel_is_not_implemented(self):
        fb = _fb(GS4_HMSB, 8, 8)
        with self.assertRaises(NotImplementedError):
            fb.pixel(0, 0, 1)

    def test_gs8_is_constructible(self):
        # GS8 can be created (depth 8); set_pixel is not usable on CPython
        # because the fallback stores bytes into a bytearray index, but the
        # constructor itself must succeed.
        fb = _fb(GS8, 8, 8)
        self.assertEqual(fb.width, 8)


if __name__ == "__main__":
    unittest.main()
