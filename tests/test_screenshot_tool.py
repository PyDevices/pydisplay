# SPDX-License-Identifier: MIT
"""Tests for the desktop example screenshot tool."""

import importlib.util
from pathlib import Path
import struct
import tempfile
import unittest

_TOOL = Path(__file__).resolve().parent.parent / "tools" / "screenshot.py"
_SPEC = importlib.util.spec_from_file_location("pydisplay_screenshot_tool", _TOOL)
screenshot = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(screenshot)


class TestScreenshotTool(unittest.TestCase):
    def test_writes_rgb_png(self):
        pixels = bytes((255, 0, 0, 0, 255, 0, 0, 0, 255, 255, 255, 255))
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "nested" / "shot.png"
            screenshot.save_rgb_png(output, pixels, 2, 2)
            data = output.read_bytes()
        self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
        self.assertEqual(struct.unpack(">II", data[16:24]), (2, 2))

    def test_resolves_example_shorthand(self):
        repo_root = Path(__file__).resolve().parent.parent
        expected = repo_root / "src" / "examples" / "logo.py"
        self.assertEqual(screenshot._resolve_example("logo", repo_root), expected)

    def test_default_output_uses_docs_screenshots(self):
        self.assertEqual(
            screenshot._default_output("src/examples/logo.py"),
            Path("docs/screenshots/logo.png"),
        )

    def test_resolution_and_scale_options(self):
        args = screenshot._parse_args(["logo", "--resolution", "240X320", "--scale", "1.5"])
        self.assertEqual(args.resolution, (240, 320))
        self.assertEqual(args.scale, 1.5)


if __name__ == "__main__":
    unittest.main()
