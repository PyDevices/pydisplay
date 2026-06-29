# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Tests for ``graphics.capabilities()``."""

import sys
import unittest

import _env  # noqa: F401

import graphics
from graphics import capabilities, framebuf_backend


class TestCapabilities(unittest.TestCase):
    def test_capabilities_returns_dict(self):
        caps = capabilities()
        self.assertIsInstance(caps, dict)
        self.assertIn("framebuf", caps)
        self.assertIn("dialect", caps)
        self.assertIn("formats", caps)

    def test_framebuf_backend_matches_capabilities(self):
        self.assertEqual(framebuf_backend(), capabilities()["framebuf"])

    def test_dialect_matches_runtime(self):
        self.assertEqual(capabilities()["dialect"], sys.implementation.name)

    def test_formats_include_rgb565(self):
        self.assertIn("RGB565", capabilities()["formats"])

    def test_cpython_uses_pure_python_framebuf(self):
        if sys.implementation.name != "cpython":
            self.skipTest("CPython-only assertion")
        self.assertEqual(capabilities()["framebuf"], "pure_python")


if __name__ == "__main__":
    unittest.main()
