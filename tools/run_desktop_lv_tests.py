#!/usr/bin/env python3
"""
Run LVGL timer/input harness on desktop Python+LVGL executables.

Thin wrapper around ``lv_timer_test_kit.py``: sync + async, strict click
checks, results in the system temp directory.

From repo root:
    python tools/run_desktop_lv_tests.py
    ./tools/run_desktop_lv_tests.py

For per-runtime selection, use ``python tools/lv_timer_test_kit.py`` instead.
"""

from __future__ import annotations

import os
from pathlib import Path
import sys
import tempfile

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))

from lv_timer_test_kit import LVGL_RUNTIMES, run_kit  # noqa: E402


def _temp_dir() -> Path:
    return Path(
        os.environ.get("TEMP")
        or os.environ.get("TMPDIR")
        or os.environ.get("TMP")
        or tempfile.gettempdir()
    )


DESKTOP_RESULTS = _temp_dir() / "desktop_lv_test_results.json"
DESKTOP_MODES = ("sync", "async")


def main() -> int:
    return run_kit(
        only=list(LVGL_RUNTIMES),
        modes=DESKTOP_MODES,
        strict_clicks=True,
        results_path=DESKTOP_RESULTS,
    )


if __name__ == "__main__":
    sys.exit(main())
