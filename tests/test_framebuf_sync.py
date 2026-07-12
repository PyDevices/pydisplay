# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Ensure the generated graphics.framebuf copy matches add_ons/framebuf.py."""

from pathlib import Path
import subprocess
import sys
import unittest

import _env  # noqa: F401


class TestFramebufSync(unittest.TestCase):
    def test_generated_graphics_framebuf_matches_canonical(self):
        repo = Path(__file__).resolve().parents[1]
        proc = subprocess.run(
            [sys.executable, "scripts/install_sync_framebuf.py", "--check"],
            cwd=repo,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(
            proc.returncode,
            0,
            msg=proc.stderr or proc.stdout or "sync_framebuf --check failed",
        )


if __name__ == "__main__":
    unittest.main()
