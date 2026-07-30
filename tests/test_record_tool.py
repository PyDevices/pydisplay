# SPDX-License-Identifier: MIT
"""Tests for the desktop example recording tool."""

import importlib.util
from pathlib import Path
import sys
import unittest

_TOOLS = Path(__file__).resolve().parent.parent / "tools"
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))
_SPEC = importlib.util.spec_from_file_location("pydisplay_record_tool", _TOOLS / "record.py")
record = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(record)


class TestRecordTool(unittest.TestCase):
    def test_default_output_uses_docs_videos(self):
        self.assertEqual(
            record._default_output("src/examples/bouncing_balls.py"),
            Path("docs/videos/bouncing_balls.mp4"),
        )

    def test_positional_duration(self):
        args = record._parse_args(["logo", "2.5", "--fps", "20"])
        self.assertEqual(args.duration, 2.5)
        self.assertEqual(args.fps, 20)


if __name__ == "__main__":
    unittest.main()
