# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Tests for displaysys.pixeldisplay."""

import unittest

import _env  # noqa: F401

from displaysys.pixeldisplay import (
    HORIZONTAL,
    PixelDisplay,
    PixelFramebuffer,
    _build_grid_mapper,
)


def _horizontal_index(x, y, width, alternating):
    if alternating and y % 2:
        return y * width + (width - 1 - x)
    return y * width + x


class MockStrip:
    def __init__(self, count):
        self.count = count
        self.data = [(0, 0, 0)] * count
        self.show_calls = 0

    def __setitem__(self, index, value):
        self.data[index] = value

    def show(self):
        self.show_calls += 1


class TestPixelGridMap(unittest.TestCase):
    def test_8x8_alternating_horizontal(self):
        _, _, indices = _build_grid_mapper(8, 8, orientation=HORIZONTAL, alternating=True)
        self.assertEqual(len(indices), 64)
        for y in range(8):
            for x in range(8):
                self.assertEqual(
                    indices[y * 8 + x],
                    _horizontal_index(x, y, 8, True),
                )

    def test_12x6_not_alternating_horizontal(self):
        _, _, indices = _build_grid_mapper(12, 6, orientation=HORIZONTAL, alternating=False)
        self.assertEqual(len(indices), 72)
        for y in range(6):
            for x in range(12):
                self.assertEqual(indices[y * 12 + x], y * 12 + x)


class TestPixelFramebuffer(unittest.TestCase):
    def test_display_writes_changed_pixels(self):
        strip = MockStrip(32)
        fb = PixelFramebuffer(strip, 8, 4, alternating=False)
        fb.fill(0xFF0000)
        fb.display()
        self.assertEqual(strip.show_calls, 1)
        self.assertEqual(strip.data[0], (255, 0, 0))
        self.assertEqual(strip.data[31], (255, 0, 0))

        fb.display()
        self.assertEqual(strip.show_calls, 2)

        fb.pixel(0, 0, 0x0000FF)
        fb.display()
        self.assertEqual(strip.data[0], (0, 0, 255))
        self.assertEqual(strip.data[1], (255, 0, 0))


class TestPixelDisplay(unittest.TestCase):
    def test_show_calls_display(self):
        class Framebuf:
            width = 4
            height = 4
            rotation = 0
            display_calls = 0

            def display(self):
                Framebuf.display_calls += 1

        buf = Framebuf()
        drv = PixelDisplay(buf)
        drv.show()
        self.assertEqual(Framebuf.display_calls, 1)

    def test_color_depth_is_16(self):
        strip = MockStrip(32)
        fb = PixelFramebuffer(strip, 8, 4, alternating=False)
        drv = PixelDisplay(fb)
        self.assertEqual(drv.color_depth, 16)

    def test_fill_rect_converts_565_to_strip_rgb(self):
        strip = MockStrip(32)
        fb = PixelFramebuffer(strip, 8, 4, alternating=False)
        drv = PixelDisplay(fb)
        drv.fill_rect(0, 0, 1, 1, 0xFFFF)
        drv.show()
        self.assertEqual(strip.data[0], (255, 255, 255))

    def test_blit_rect_converts_565_buffer(self):
        strip = MockStrip(32)
        fb = PixelFramebuffer(strip, 8, 4, alternating=False)
        drv = PixelDisplay(fb)
        buf = bytes((0x00, 0xF8))  # 565 red, little-endian
        drv.blit_rect(buf, 1, 0, 1, 1)
        drv.show()
        self.assertEqual(strip.data[1], (255, 0, 0))


if __name__ == "__main__":
    unittest.main()
