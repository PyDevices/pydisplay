# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Tests for graphics blit hook dispatch."""

import unittest

import _env  # noqa: F401
from _support import make_fb

from graphics import Area, Draw, blit, blit_rect
from graphics._blit_hooks import (
    blit_rect_dispatch,
    canvas_accepts_blit_rect,
    canvas_accepts_blit_transparent,
    try_fast_framebuffer_blit,
)


class _BlitRectCanvas:
    color_depth = 16

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.calls = []

    def blit_rect(self, buf, x, y, w, h):
        self.calls.append((bytes(buf), x, y, w, h))


class _BlitTransparentCanvas(_BlitRectCanvas):
    def __init__(self, width, height):
        super().__init__(width, height)
        self.transparent_calls = []

    def blit_transparent(self, buf, x, y, w, h, key):
        self.transparent_calls.append((bytes(buf), x, y, w, h, key))


class TestBlitHooks(unittest.TestCase):
    def test_framebuffer_rejects_rect_hook(self):
        fb = make_fb(w=8, h=8)
        self.assertFalse(canvas_accepts_blit_rect(fb))
        self.assertFalse(canvas_accepts_blit_transparent(fb))

    def test_display_like_canvas_accepts_hooks(self):
        canvas = _BlitRectCanvas(16, 16)
        self.assertTrue(canvas_accepts_blit_rect(canvas))
        canvas = _BlitTransparentCanvas(16, 16)
        self.assertTrue(canvas_accepts_blit_transparent(canvas))

    def test_draw_blit_uses_display_blit_rect(self):
        src = make_fb(w=4, h=4)
        src.fill(0xBEEF)
        display = _BlitRectCanvas(16, 16)
        draw = Draw(display)
        area = draw.blit(src, 2, 2)
        self.assertEqual(area, Area(2, 2, 4, 4))
        self.assertEqual(len(display.calls), 1)
        _buf, x, y, w, h = display.calls[0]
        self.assertEqual((x, y, w, h), (2, 2, 4, 4))
        self.assertEqual(len(_buf), 4 * 4 * 2)

    def test_blit_rect_dispatch_to_display(self):
        canvas = _BlitRectCanvas(8, 8)
        buf = bytearray(2 * 2 * 2)
        blit_rect_dispatch(canvas, buf, 1, 1, 2, 2)
        self.assertEqual(len(canvas.calls), 1)

    def test_blit_rect_dispatch_to_framebuffer(self):
        dst = make_fb(w=8, h=8)
        dst.fill(0)
        buf = bytearray([0x34, 0x12, 0x78, 0x56])
        blit_rect(dst, buf, 1, 1, 2, 1)
        self.assertEqual(dst.pixel(1, 1), 0x1234)
        self.assertEqual(dst.pixel(2, 1), 0x5678)

    def test_try_fast_framebuffer_blit_clips(self):
        src = make_fb(w=4, h=4)
        src.fill(0x00FF)
        dst = make_fb(w=8, h=8)
        dst.fill(0)
        area = try_fast_framebuffer_blit(dst, src, 6, 6)
        self.assertEqual(area, Area(6, 6, 2, 2))
        self.assertEqual(dst.pixel(6, 6), 0x00FF)
        self.assertEqual(dst.pixel(7, 7), 0x00FF)
        self.assertEqual(dst.pixel(5, 5), 0)

    def test_blit_transparent_uses_display_hook(self):
        from graphics import blit_transparent

        canvas = _BlitTransparentCanvas(8, 8)
        buf = bytearray(2 * 2 * 2)
        blit_transparent(canvas, buf, 0, 0, 2, 2, 0)
        self.assertEqual(len(canvas.transparent_calls), 1)

    def test_framebuffer_blit_rect_no_recursion(self):
        dst = make_fb(w=8, h=8)
        buf = bytearray(2 * 2 * 2)
        area = dst.blit_rect(buf, 0, 0, 2, 2)
        self.assertEqual(area, Area(0, 0, 2, 2))


if __name__ == "__main__":
    unittest.main()
