# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Tests for ``graphics`` image file I/O (save / from_file and the converters).

Covers the formats whose pure-Python read/write paths round-trip cleanly on
CPython: PBM (MONO_HLSB) and PGM (grayscale).
"""

import os
import tempfile
import unittest

import _env  # noqa: F401

from graphics import (
    GS2_HMSB,
    GS8,
    MONO_HLSB,
    RGB565,
    FrameBuffer,
    pbm_to_framebuffer,
    pgm_to_framebuffer,
)


class _TmpDirTest(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.mkdtemp(prefix="graphics_files_")

    def tearDown(self):
        import shutil

        shutil.rmtree(self._dir, ignore_errors=True)

    def _path(self, name):
        return os.path.join(self._dir, name)


class TestSaveLoadRoundTrip(_TmpDirTest):
    def test_pbm_roundtrip(self):
        fb = FrameBuffer(bytearray((16 + 7) // 8 * 8), 16, 8, MONO_HLSB)
        fb.fill(0)
        fb.fill_rect(1, 1, 3, 3, 1)
        path = self._path("img.pbm")
        fb.save(path)

        loaded = FrameBuffer.from_file(path)
        self.assertEqual(loaded.width, 16)
        self.assertEqual(loaded.height, 8)
        self.assertEqual(loaded.format, MONO_HLSB)
        self.assertEqual(bytes(loaded.buffer), bytes(fb.buffer))
        self.assertEqual(loaded.pixel(2, 2), 1)

    def test_pgm_roundtrip(self):
        # Build via per-pixel writes (GS2 fill() would convert the buffer to a
        # list, which save cannot serialise).
        fb = FrameBuffer(bytearray((16 + 3) // 4 * 8), 16, 8, GS2_HMSB)
        fb.fill_rect(1, 1, 3, 3, 3)
        path = self._path("img.pgm")
        fb.save(path)

        loaded = FrameBuffer.from_file(path)
        self.assertEqual(loaded.width, 16)
        self.assertEqual(loaded.height, 8)
        self.assertEqual(loaded.format, GS2_HMSB)
        self.assertEqual(bytes(loaded.buffer), bytes(fb.buffer))
        self.assertEqual(loaded.pixel(2, 2), 3)

    def test_save_appends_extension(self):
        fb = FrameBuffer(bytearray((8 + 7) // 8 * 8), 8, 8, MONO_HLSB)
        fb.fill(0)
        fb.save(self._path("noext"))
        self.assertTrue(os.path.exists(self._path("noext.pbm")))

    def test_rgb565_saves_bmp_signature(self):
        fb = FrameBuffer(bytearray(8 * 8 * 2), 8, 8, RGB565)
        fb.fill(0x1234)
        path = self._path("img.bmp")
        fb.save(path)
        with open(path, "rb") as f:
            self.assertEqual(f.read(2), b"BM")


class TestConverters(_TmpDirTest):
    def test_pbm_to_framebuffer(self):
        path = self._path("hand.pbm")
        with open(path, "wb") as f:
            f.write(b"P4\n2 2\n")
            f.write(bytes([0b11000000, 0b00000000]))  # 1 byte per row, 2 rows
        fb = pbm_to_framebuffer(path)
        self.assertEqual((fb.width, fb.height), (2, 2))
        self.assertEqual(fb.format, MONO_HLSB)
        self.assertEqual(fb.pixel(0, 0), 1)
        self.assertEqual(fb.pixel(0, 1), 0)

    def test_pgm_to_framebuffer_gs8(self):
        path = self._path("hand.pgm")
        with open(path, "wb") as f:
            f.write(b"P5\n2 2\n255\n")
            f.write(bytes([10, 20, 30, 40]))
        fb = pgm_to_framebuffer(path)
        self.assertEqual((fb.width, fb.height), (2, 2))
        self.assertEqual(fb.format, GS8)
        self.assertEqual(fb.pixel(0, 0), 10)
        self.assertEqual(fb.pixel(1, 1), 40)

    def test_pbm_bad_magic_raises(self):
        path = self._path("bad.pbm")
        with open(path, "wb") as f:
            f.write(b"XX\n1 1\n\x00")
        with self.assertRaises(ValueError):
            pbm_to_framebuffer(path)


class TestFromFileDispatch(_TmpDirTest):
    def test_unknown_header_raises(self):
        path = self._path("bad.dat")
        with open(path, "wb") as f:
            f.write(b"ZZ1234")
        with self.assertRaises(ValueError):
            FrameBuffer.from_file(path)


if __name__ == "__main__":
    unittest.main()
