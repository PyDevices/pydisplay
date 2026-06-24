# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Tests for ``displaysys.fbdisplay.FBDisplay``.

A :class:`_support.FakeFrameBuffer` stands in for a real CircuitPython
framebuffer so the pixel-pushing paths can be checked byte-for-byte.
"""

import unittest

import _env  # noqa: F401
from _support import make_fbdisplay


class TestFBDisplayDrawing(unittest.TestCase):
    def test_fill_rect_writes_little_endian(self):
        d, fb = make_fbdisplay(4, 2)
        # 0xF800 -> little-endian bytes 0x00, 0xF8
        d.fill_rect(0, 0, 2, 1, 0xF800)
        self.assertEqual(bytes(fb.data[:8]), b"\x00\xf8\x00\xf8\x00\x00\x00\x00")

    def test_fill_rect_returns_bounds(self):
        d, _ = make_fbdisplay(8, 8)
        self.assertEqual(d.fill_rect(1, 2, 3, 4, 0x1234), (1, 2, 3, 4))

    def test_fill_covers_whole_buffer(self):
        d, fb = make_fbdisplay(4, 4)
        d.fill(0xFFFF)
        self.assertEqual(bytes(fb.data), b"\xff\xff" * 16)

    def test_pixel_sets_single_cell(self):
        d, fb = make_fbdisplay(4, 4)
        d.pixel(1, 0, 0x07E0)  # green -> little-endian 0xE0, 0x07
        self.assertEqual(bytes(fb.data[2:4]), b"\xe0\x07")
        # neighbouring pixels untouched
        self.assertEqual(bytes(fb.data[0:2]), b"\x00\x00")
        self.assertEqual(bytes(fb.data[4:6]), b"\x00\x00")

    def test_blit_rect_copies_source(self):
        d, fb = make_fbdisplay(4, 2)
        src = bytearray(b"\x01\x02\x03\x04")  # 2 pixels wide, 1 tall
        d.blit_rect(src, 0, 0, 2, 1)
        self.assertEqual(bytes(fb.data[:4]), b"\x01\x02\x03\x04")

    def test_blit_rect_rejects_out_of_range(self):
        d, _ = make_fbdisplay(4, 2)
        with self.assertRaises(ValueError):
            d.blit_rect(bytearray(2), 3, 0, 2, 1)  # runs off the right edge

    def test_blit_rect_rejects_wrong_buffer_size(self):
        d, _ = make_fbdisplay(4, 2)
        with self.assertRaises(ValueError):
            d.blit_rect(bytearray(2), 0, 0, 2, 1)  # needs 4 bytes, got 2

    def test_show_refreshes_backing_framebuffer(self):
        d, fb = make_fbdisplay(4, 2)
        self.assertEqual(fb.refresh_count, 0)
        d.show()
        d.show()
        self.assertEqual(fb.refresh_count, 2)


class TestFBDisplayByteswap(unittest.TestCase):
    def test_byteswap_buffer_swaps_when_enabled(self):
        # reverse_bytes_in_word=True -> requires_byteswap and auto byteswap on
        d, fb = make_fbdisplay(4, 2, reverse_bytes_in_word=True)
        self.assertTrue(d.requires_byteswap)
        self.assertTrue(d._auto_byteswap)
        src = bytearray(b"\x01\x02\x03\x04")
        d.blit_rect(src, 0, 0, 2, 1)
        # blit_rect byteswaps the source in place before copying
        self.assertEqual(bytes(fb.data[:4]), b"\x02\x01\x04\x03")

    def test_fill_rect_big_endian_when_byteswap_enabled(self):
        d, fb = make_fbdisplay(4, 2, reverse_bytes_in_word=True)
        d.fill_rect(0, 0, 1, 1, 0xF800)  # big-endian bytes 0xF8, 0x00
        self.assertEqual(bytes(fb.data[:2]), b"\xf8\x00")


class TestBlitTransparent(unittest.TestCase):
    def test_skips_key_colored_pixels(self):
        d, fb = make_fbdisplay(4, 1)
        nonkey = b"\x34\x12"  # 0x1234
        key = b"\x00\x00"  # transparent color key 0x0000
        buf = bytearray(nonkey + key + nonkey + key)
        result = d.blit_transparent(buf, 0, 0, 4, 1, 0x0000)
        self.assertEqual(result, (0, 0, 4, 1))
        # only columns 0 and 2 written; columns 1 and 3 stay transparent
        self.assertEqual(bytes(fb.data), nonkey + key + nonkey + key)


if __name__ == "__main__":
    unittest.main()
