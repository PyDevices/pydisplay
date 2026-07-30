# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""PGDisplay frame recording via displaysys."""

import unittest

import _env  # noqa: F401
from _support import quiet


class TestFrameRecorderBase(unittest.TestCase):
    def test_fbdisplay_has_no_frame_recorder(self):
        with quiet():
            from _support import make_fbdisplay

            d, _ = make_fbdisplay(8, 4)
        self.assertFalse(hasattr(d, "open_frame_recorder"))


if __name__ == "__main__":
    unittest.main()
