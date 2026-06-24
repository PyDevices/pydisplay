# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Tests for the color helpers and ``alloc_buffer`` in ``displaysys``."""

import unittest

import _env  # noqa: F401

from displaysys import (
    alloc_buffer,
    color332,
    color565,
    color565_swapped,
    color_rgb,
)


class TestColor565(unittest.TestCase):
    def test_primary_colors(self):
        self.assertEqual(color565(0, 0, 0), 0x0000)
        self.assertEqual(color565(255, 255, 255), 0xFFFF)
        self.assertEqual(color565(255, 0, 0), 0xF800)
        self.assertEqual(color565(0, 255, 0), 0x07E0)
        self.assertEqual(color565(0, 0, 255), 0x001F)

    def test_accepts_sequence(self):
        self.assertEqual(color565((255, 255, 255)), 0xFFFF)
        self.assertEqual(color565([255, 0, 0]), 0xF800)

    def test_extra_sequence_items_ignored(self):
        # a 4-tuple (e.g. RGBA) keeps only the first three components
        self.assertEqual(color565((255, 0, 0, 99)), 0xF800)

    def test_result_fits_in_16_bits(self):
        self.assertEqual(color565(255, 255, 255) & ~0xFFFF, 0)


class TestColor565Swapped(unittest.TestCase):
    def test_is_byte_swap_of_color565(self):
        for rgb in [(0, 0, 0), (255, 255, 255), (255, 0, 0), (12, 34, 56)]:
            c = color565(*rgb)
            expected = ((c & 0xFF) << 8) | ((c & 0xFF00) >> 8)
            self.assertEqual(color565_swapped(*rgb), expected)

    def test_accepts_sequence(self):
        self.assertEqual(color565_swapped((255, 0, 0)), color565_swapped(255, 0, 0))


class TestColor332(unittest.TestCase):
    def test_primary_colors(self):
        self.assertEqual(color332(0, 0, 0), 0x00)
        self.assertEqual(color332(255, 255, 255), 0xFF)
        self.assertEqual(color332(255, 0, 0), 0xE0)
        self.assertEqual(color332(0, 255, 0), 0x1C)
        self.assertEqual(color332(0, 0, 255), 0x03)

    def test_result_fits_in_8_bits(self):
        self.assertEqual(color332(255, 255, 255) & ~0xFF, 0)


class TestColorRgb(unittest.TestCase):
    def test_int_extremes(self):
        self.assertEqual(color_rgb(0x0000), (0, 0, 0))
        self.assertEqual(color_rgb(0xFFFF), (255, 255, 255))

    def test_passthrough_three_tuple(self):
        self.assertEqual(color_rgb((10, 20, 30)), (10, 20, 30))

    def test_two_byte_sequence(self):
        # same low/high bytes as the int form of pure red (0xF800)
        self.assertEqual(color_rgb(bytes((0x00, 0xF8))), (255, 0, 0))

    def test_round_trips_black_and_white_exactly(self):
        self.assertEqual(color_rgb(color565(0, 0, 0)), (0, 0, 0))
        self.assertEqual(color_rgb(color565(255, 255, 255)), (255, 255, 255))

    def test_round_trip_is_lossy_for_primaries(self):
        # RGB565 packs 5/6/5 bits, so expanding back is only approximate and
        # adjacent channels can bleed in from the shared low byte.
        self.assertEqual(color_rgb(color565(255, 0, 0)), (255, 0, 0))
        self.assertEqual(color_rgb(color565(0, 255, 0)), (0, 252, 0))
        self.assertEqual(color_rgb(color565(0, 0, 255)), (0, 3, 255))


class TestAllocBuffer(unittest.TestCase):
    def test_size_and_zeroed(self):
        buf = alloc_buffer(16)
        self.assertEqual(len(buf), 16)
        self.assertEqual(bytes(buf), b"\x00" * 16)

    def test_is_writable_memoryview(self):
        buf = alloc_buffer(4)
        self.assertIsInstance(buf, memoryview)
        buf[0] = 0xAB
        self.assertEqual(buf[0], 0xAB)


if __name__ == "__main__":
    unittest.main()
