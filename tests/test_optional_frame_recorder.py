# SPDX-License-Identifier: MIT
"""The optional recorder must not be needed for ordinary display imports."""

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class TestOptionalFrameRecorder(unittest.TestCase):
    def test_sdldisplay_imports_without_add_ons(self):
        repo_root = Path(__file__).resolve().parent.parent
        env = os.environ.copy()
        env["PYTHONPATH"] = str(repo_root / "src" / "lib")
        code = (
            "import sys; import displaysys.sdldisplay; assert 'frame_recorder' not in sys.modules"
        )
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                [sys.executable, "-c", code],
                cwd=tmp,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
