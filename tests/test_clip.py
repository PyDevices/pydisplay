# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Tests for clip-region helpers."""

import unittest

import _env  # noqa: F401
from _support import make_fb

from graphics import Area
from graphics._clip import ClippedCanvas, crop_rgb565_buffer, intersect_rect


class TestClipHelpers(unittest.TestCase):
    def test_intersect_rect(self):
        self.assertEqual(
            intersect_rect(0, 0, 10, 10, Area(5, 5, 10, 10)),
            Area(5, 5, 5, 5),
        )
        self.assertIsNone(intersect_rect(0, 0, 2, 2, Area(10, 10, 2, 2)))

    def test_crop_rgb565_buffer(self):
        buf = bytearray([0, 1, 2, 3, 4, 5, 6, 7])
        cropped = crop_rgb565_buffer(buf, 2, 1, 0, 1, 2)
        self.assertEqual(bytes(cropped), bytes([2, 3, 6, 7]))

    def test_clipped_canvas_fill_rect(self):
        fb = make_fb(w=8, h=8)
        fb.fill(0)
        clipped = ClippedCanvas(fb, Area(2, 2, 3, 3))
        clipped.fill_rect(0, 0, 8, 8, 0xFFFF)
        self.assertEqual(fb.pixel(1, 1), 0)
        self.assertEqual(fb.pixel(2, 2), 0xFFFF)
        self.assertEqual(fb.pixel(4, 4), 0xFFFF)
        self.assertEqual(fb.pixel(5, 5), 0)


if __name__ == "__main__":
    unittest.main()
