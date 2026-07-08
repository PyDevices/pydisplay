# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Tests for manifest-driven board_config generation."""

from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
GEN = ROOT / "scripts" / "generate_board_configs.py"
PYTHON = sys.executable


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
        self.assertRegex(proc.stdout, r"OK \(\d+ manifest\(s\)\)")

    def test_board_configs_has_no_stray_files(self):
        proc = self._run("--check")
        self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout)
        stray = [
            p
            for p in (ROOT / "board_configs").rglob("*")
            if p.is_file() and p.name not in ("board_config.py", "package.json")
        ]
        self.assertEqual(stray, [])

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
