# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Tests for the pure-Python ``framebuf`` module (Damien-parity, MP-pure).

This mirrors MicroPython's ``extmod/modframebuf.c`` behavior on CPython: every
drawing method returns ``None`` (like the compiled MicroPython module), not a
tuple or ``Area``. ``graphics._framebuf_plus`` wraps this base class to add
``Area`` bounding boxes and pydisplay extensions.
"""

import unittest

import _env  # noqa: F401
from framebuf import (
    GS2_HMSB,
    GS4_HMSB,
    GS8,
    MONO_HLSB,
    MONO_HMSB,
    MONO_VLSB,
    MVLSB,
    RGB565,
    FrameBuffer,
)

# Formats whose pure-Python get/set round-trip cleanly on CPython.
_ROUNDTRIP_FORMATS = (MONO_VLSB, MONO_HLSB, MONO_HMSB, RGB565, GS2_HMSB, GS4_HMSB, GS8)


def _fb(format, w=16, h=16):
    return FrameBuffer(bytearray(w * h * 3 + 64), w, h, format)


class TestFrameBufferBasics(unittest.TestCase):
    def test_invalid_format_raises(self):
        with self.assertRaises(ValueError):
            FrameBuffer(bytearray(16), 4, 4, 99)

    def test_invalid_dimensions_raise(self):
        with self.assertRaises(ValueError):
            FrameBuffer(bytearray(16), 0, 4, RGB565)
        with self.assertRaises(ValueError):
            FrameBuffer(bytearray(16), 4, 0, RGB565)

    def test_mvlsb_alias(self):
        self.assertEqual(MVLSB, MONO_VLSB)

    def test_width_height_properties(self):
        fb = _fb(RGB565, 12, 7)
        self.assertEqual(fb.width, 12)
        self.assertEqual(fb.height, 7)

    def test_pixel_set_returns_none(self):
        fb = _fb(RGB565)
        result = fb.pixel(1, 1, 0x1234)
        self.assertIsNone(result)

    def test_pixel_out_of_bounds_returns_none(self):
        fb = _fb(RGB565, 8, 8)
        self.assertIsNone(fb.pixel(-1, 0))
        self.assertIsNone(fb.pixel(8, 0))
        self.assertIsNone(fb.pixel(0, 8))

    def test_pixel_set_out_of_bounds_is_noop(self):
        fb = _fb(RGB565, 8, 8)
        fb.fill(0)
        # Out-of-bounds set must not raise and must not touch the buffer.
        fb.pixel(-1, 0, 0xFFFF)
        fb.pixel(8, 0, 0xFFFF)
        fb.pixel(0, 8, 0xFFFF)
        self.assertTrue(all(b == 0 for b in fb._buffer[: 8 * 8 * 2]))


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

    def test_gs4_nibble_packing(self):
        fb = _fb(GS4_HMSB, 8, 8)
        fb.pixel(0, 0, 0x3)
        fb.pixel(1, 0, 0xC)
        self.assertEqual(fb.pixel(0, 0), 0x3)
        self.assertEqual(fb.pixel(1, 0), 0xC)

    def test_gs8_roundtrip(self):
        fb = _fb(GS8, 8, 8)
        fb.pixel(3, 3, 0xAB)
        self.assertEqual(fb.pixel(3, 3), 0xAB)
        self.assertEqual(fb.pixel(2, 3), 0)


class TestFrameBufferFill(unittest.TestCase):
    def test_fill_sets_every_pixel(self):
        fb = _fb(RGB565, 8, 8)
        fb.fill(0x07E0)
        self.assertTrue(all(fb.pixel(x, y) == 0x07E0 for x in range(8) for y in range(8)))

    def test_fill_returns_none(self):
        fb = _fb(RGB565, 8, 8)
        self.assertIsNone(fb.fill(0))

    def test_fill_rect_returns_none(self):
        fb = _fb(RGB565, 8, 8)
        self.assertIsNone(fb.fill_rect(0, 0, 1, 1, 0))

    def test_fill_rect_region(self):
        fb = _fb(RGB565, 8, 8)
        fb.fill(0)
        fb.fill_rect(2, 2, 3, 3, 0xFFFF)
        self.assertEqual(fb.pixel(2, 2), 0xFFFF)
        self.assertEqual(fb.pixel(4, 4), 0xFFFF)
        self.assertEqual(fb.pixel(5, 5), 0)
        self.assertEqual(fb.pixel(1, 1), 0)

    def test_fill_rect_clips_to_bounds(self):
        fb = _fb(RGB565, 8, 8)
        fb.fill(0)
        # Fully out of range: no-op, no exception.
        fb.fill_rect(-10, -10, 2, 2, 0xFFFF)
        fb.fill_rect(20, 20, 2, 2, 0xFFFF)
        # Partially out of range: clipped, no exception.
        fb.fill_rect(-2, -2, 4, 4, 0xFFFF)
        self.assertEqual(fb.pixel(0, 0), 0xFFFF)
        fb.fill_rect(6, 6, 4, 4, 0xFFFF)
        self.assertEqual(fb.pixel(7, 7), 0xFFFF)

    def test_fill_rect_gs4_matches_pixel_loop(self):
        fb = _fb(GS4_HMSB, 8, 8)
        fb.fill(0)
        fb.fill_rect(1, 1, 3, 3, 0xA)
        for x in range(1, 4):
            for y in range(1, 4):
                self.assertEqual(fb.pixel(x, y), 0xA)
        self.assertEqual(fb.pixel(0, 0), 0)
        self.assertEqual(fb.pixel(4, 4), 0)


class TestFrameBufferShapes(unittest.TestCase):
    def setUp(self):
        self.fb = _fb(RGB565, 16, 16)
        self.fb.fill(0)

    def test_hline_returns_none(self):
        self.assertIsNone(self.fb.hline(0, 0, 5, 0xFFFF))
        self.assertTrue(all(self.fb.pixel(x, 0) == 0xFFFF for x in range(5)))

    def test_vline_returns_none(self):
        self.assertIsNone(self.fb.vline(0, 0, 5, 0xFFFF))
        self.assertTrue(all(self.fb.pixel(0, y) == 0xFFFF for y in range(5)))

    def test_rect_outline_is_hollow(self):
        self.assertIsNone(self.fb.rect(2, 2, 6, 6, 0xFFFF))
        self.assertEqual(self.fb.pixel(2, 2), 0xFFFF)
        self.assertEqual(self.fb.pixel(7, 7), 0xFFFF)
        self.assertEqual(self.fb.pixel(4, 4), 0)

    def test_rect_filled(self):
        self.fb.rect(2, 2, 6, 6, 0xFFFF, True)
        self.assertEqual(self.fb.pixel(4, 4), 0xFFFF)

    def test_line_returns_none(self):
        self.assertIsNone(self.fb.line(0, 0, 5, 5, 0xFFFF))
        self.assertEqual(self.fb.pixel(0, 0), 0xFFFF)
        self.assertEqual(self.fb.pixel(5, 5), 0xFFFF)

    def test_line_horizontal(self):
        self.fb.line(1, 1, 6, 1, 0xFFFF)
        self.assertTrue(all(self.fb.pixel(x, 1) == 0xFFFF for x in range(1, 7)))

    def test_ellipse_returns_none(self):
        self.assertIsNone(self.fb.ellipse(8, 8, 3, 3, 0xFFFF))
        # A circle of radius 3 touches the point directly right of center.
        self.assertEqual(self.fb.pixel(11, 8), 0xFFFF)

    def test_ellipse_filled_center_set(self):
        self.fb.ellipse(8, 8, 3, 3, 0xFFFF, True)
        self.assertEqual(self.fb.pixel(8, 8), 0xFFFF)

    def test_ellipse_zero_radius_sets_one_pixel(self):
        self.fb.ellipse(5, 5, 0, 0, 0xFFFF)
        self.assertEqual(self.fb.pixel(5, 5), 0xFFFF)

    def test_poly_outline_flat_list(self):
        self.assertIsNone(self.fb.poly(0, 0, [2, 2, 8, 2, 8, 8, 2, 8], 0xFFFF))
        self.assertEqual(self.fb.pixel(2, 2), 0xFFFF)
        self.assertEqual(self.fb.pixel(8, 2), 0xFFFF)

    def test_poly_outline_tuple_pairs(self):
        self.fb.poly(0, 0, [(2, 2), (8, 2), (8, 8), (2, 8)], 0xFFFF)
        self.assertEqual(self.fb.pixel(2, 2), 0xFFFF)

    def test_poly_filled_interior(self):
        self.fb.poly(0, 0, [2, 2, 12, 2, 12, 12, 2, 12], 0xFFFF, True)
        self.assertEqual(self.fb.pixel(6, 6), 0xFFFF)
        self.assertEqual(self.fb.pixel(0, 0), 0)


class TestFrameBufferScroll(unittest.TestCase):
    def test_scroll_moves_pixels(self):
        fb = _fb(RGB565, 8, 8)
        fb.fill(0)
        fb.pixel(0, 0, 0xFFFF)
        self.assertIsNone(fb.scroll(2, 3))
        self.assertEqual(fb.pixel(2, 3), 0xFFFF)

    def test_scroll_supports_mono_vlsb(self):
        # MicroPython's scroll works pixel-by-pixel for any depth, including
        # sub-byte MONO_VLSB -- unlike a byte-copy shortcut, it must not raise.
        fb = _fb(MONO_VLSB, 8, 8)
        fb.fill(0)
        fb.pixel(1, 1, 1)
        fb.scroll(1, 1)
        self.assertEqual(fb.pixel(2, 2), 1)

    def test_scroll_large_step_is_noop(self):
        fb = _fb(RGB565, 8, 8)
        fb.fill(0)
        fb.pixel(0, 0, 0xFFFF)
        fb.scroll(100, 0)
        # Step >= width is a no-op per MicroPython semantics.
        self.assertEqual(fb.pixel(0, 0), 0xFFFF)


class TestFrameBufferBlit(unittest.TestCase):
    def test_blit_copies_pixels(self):
        dst = _fb(RGB565, 8, 8)
        dst.fill(0)
        src = _fb(RGB565, 4, 4)
        src.fill(0xABCD)
        self.assertIsNone(dst.blit(src, 2, 2))
        self.assertEqual(dst.pixel(2, 2), 0xABCD)
        self.assertEqual(dst.pixel(5, 5), 0xABCD)
        self.assertEqual(dst.pixel(6, 6), 0)

    def test_blit_key_transparency(self):
        dst = _fb(RGB565, 8, 8)
        dst.fill(0x1111)
        src = _fb(RGB565, 2, 2)
        src.fill(0xABCD)
        src.pixel(0, 0, 0x2222)
        dst.blit(src, 0, 0, key=0xABCD)
        self.assertEqual(dst.pixel(0, 0), 0x2222)
        self.assertEqual(dst.pixel(1, 1), 0x1111)  # keyed out, unchanged

    def test_blit_accepts_readonly_tuple_source(self):
        dst = _fb(RGB565, 8, 8)
        dst.fill(0)
        buf = bytearray(4 * 4 * 2)
        RGB565Buf = FrameBuffer(buf, 4, 4, RGB565)
        RGB565Buf.fill(0x4321)
        dst.blit((buf, 4, 4, RGB565), 1, 1)
        self.assertEqual(dst.pixel(1, 1), 0x4321)

    def test_blit_out_of_bounds_is_noop(self):
        dst = _fb(RGB565, 8, 8)
        dst.fill(0)
        src = _fb(RGB565, 4, 4)
        src.fill(0xFFFF)
        self.assertIsNone(dst.blit(src, 100, 100))
        self.assertTrue(all(b == 0 for b in dst._buffer))


class TestFrameBufferText(unittest.TestCase):
    def test_text_returns_none(self):
        fb = _fb(RGB565, 32, 16)
        fb.fill(0)
        self.assertIsNone(fb.text("A", 0, 0, 0xFFFF))
        # 'A' glyph has at least one lit pixel in its 8x8 cell.
        self.assertTrue(any(fb.pixel(x, y) == 0xFFFF for x in range(8) for y in range(8)))

    def test_text_default_color_is_one(self):
        fb = _fb(MONO_HLSB, 32, 16)
        fb.fill(0)
        fb.text("A", 0, 0)
        self.assertTrue(any(fb.pixel(x, y) == 1 for x in range(8) for y in range(8)))

    def test_text_out_of_range_char_uses_fallback_glyph(self):
        fb = _fb(RGB565, 32, 16)
        fb.fill(0)
        fb.text(chr(200), 0, 0, 0xFFFF)
        # Falls back to glyph 127, which is a checkerboard pattern (non-blank).
        self.assertTrue(any(fb.pixel(x, y) == 0xFFFF for x in range(8) for y in range(8)))

    def test_text_columns_advance_without_gaps(self):
        fb = _fb(RGB565, 32, 16)
        fb.fill(0)
        fb.text("II", 0, 0, 0xFFFF)
        # Two 8px-wide glyphs are placed with zero gap: second glyph starts at x=8.
        col0_lit = any(fb.pixel(x, y) == 0xFFFF for x in range(8) for y in range(8))
        col1_lit = any(fb.pixel(x, y) == 0xFFFF for x in range(8, 16) for y in range(8))
        self.assertTrue(col0_lit)
        self.assertTrue(col1_lit)


class TestFormatsMatchReference(unittest.TestCase):
    """Regression tests for bit-packing bugs found while auditing against modframebuf.c."""

    def test_mhmsb_pixel_bit_order(self):
        # MONO_HMSB: bit 0 of each byte is the *leftmost* pixel of its 8-wide group.
        fb = _fb(MONO_HMSB, 8, 8)
        fb.fill(0)
        fb.pixel(0, 0, 1)
        self.assertEqual(fb._buffer[0] & 0x01, 0x01)
        self.assertEqual(fb.pixel(0, 0), 1)
        self.assertEqual(fb.pixel(1, 0), 0)

    def test_mhlsb_pixel_bit_order(self):
        # MONO_HLSB: bit 0 of each byte is the *rightmost* pixel of its 8-wide group.
        fb = _fb(MONO_HLSB, 8, 8)
        fb.fill(0)
        fb.pixel(7, 0, 1)
        self.assertEqual(fb._buffer[0] & 0x01, 0x01)
        self.assertEqual(fb.pixel(7, 0), 1)
        self.assertEqual(fb.pixel(6, 0), 0)

    def test_mhlsb_fill_rect_matches_pixel_loop(self):
        fb_a = _fb(MONO_HLSB, 16, 16)
        fb_b = _fb(MONO_HLSB, 16, 16)
        fb_a.fill(0)
        fb_b.fill(0)
        fb_a.fill_rect(3, 2, 5, 4, 1)
        for x in range(3, 8):
            for y in range(2, 6):
                fb_b.pixel(x, y, 1)
        self.assertEqual(bytes(fb_a._buffer), bytes(fb_b._buffer))

    def test_mhmsb_fill_rect_matches_pixel_loop(self):
        fb_a = _fb(MONO_HMSB, 16, 16)
        fb_b = _fb(MONO_HMSB, 16, 16)
        fb_a.fill(0)
        fb_b.fill(0)
        fb_a.fill_rect(3, 2, 5, 4, 1)
        for x in range(3, 8):
            for y in range(2, 6):
                fb_b.pixel(x, y, 1)
        self.assertEqual(bytes(fb_a._buffer), bytes(fb_b._buffer))

    def test_gs2_fill_preserves_buffer_type(self):
        fb = _fb(GS2_HMSB, 8, 8)
        fb.fill(3)
        self.assertIsInstance(fb._buffer, bytearray)
        self.assertEqual(fb.pixel(0, 0), 3)

    def test_gs8_fill_preserves_buffer_identity(self):
        fb = _fb(GS8, 8, 8)
        buf = fb._buffer
        fb.fill(5)
        self.assertIs(fb._buffer, buf)
        self.assertEqual(fb.pixel(0, 0), 5)

    def test_mono_vlsb_stride_defaults_to_width(self):
        # MicroPython does not round MONO_VLSB stride to a byte boundary (only
        # height is padded internally); stride == width unless overridden.
        fb = _fb(MONO_VLSB, 5, 8)
        self.assertEqual(fb._stride, 5)


if __name__ == "__main__":
    unittest.main()
