# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Tests for manifest-driven board_config generation."""

from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
GEN = ROOT / "scripts" / "generate_board_configs.py"
PYTHON = ROOT / ".venv" / "bin" / "python"


class TestGenerateBoardConfigs(unittest.TestCase):
    def _run(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [str(PYTHON), str(GEN), *args],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_all_manifests_check_passes(self):
        proc = self._run("--check")
        self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout)
        self.assertIn("OK (53 manifest(s))", proc.stdout)

    def test_epaper_wrapper_delegates(self):
        proc = subprocess.run(
            [str(PYTHON), str(ROOT / "scripts" / "generate_epaper_board_configs.py"), "--check"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout)


if __name__ == "__main__":
    unittest.main()
