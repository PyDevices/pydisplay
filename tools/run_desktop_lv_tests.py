#!/usr/bin/env python3
"""
Run LVGL timer/input harness on all desktop Python+LVGL executables.

Nine sequential runs (queued + async per runtime; async omitted on MicroPython
Windows). Each subprocess runs the harness from pydisplay/src (~4 s of checks,
then injected ``events.Quit``); the child should print KIT_RESULT= and exit 0.

From repo root:
    python tools/run_desktop_lv_tests.py
    ./tools/run_desktop_lv_tests.py

From src/:
    ../tools/run_desktop_lv_tests.py
"""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import sys

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "src"

# Add tools/ so lv_timer_test_kit can be imported when run as a script.
sys.path.insert(0, str(REPO / "tools"))

from lv_timer_test_kit import (  # noqa: E402
    DEFAULT_TIMEOUT,
    compute_exit_code,
    print_table,
    run_case,
)


def _cpython_venv_exe() -> str:
    return str(REPO / ".venv" / "bin" / "python")


EXECUTABLES: dict[str, list[str]] = {
    "micropython": ["micropython"],
    "circuitpython": ["circuitpython"],
    "micropython.exe": ["micropython.exe"],
    "python.exe": ["python.exe"],
    "cpython-venv": [_cpython_venv_exe()],
}

DESKTOP_MODES = ("queued", "async")

DESKTOP_RUNS: list[tuple[str, str]] = [
    ("micropython", "queued"),
    ("micropython", "async"),
    ("circuitpython", "queued"),
    ("circuitpython", "async"),
    ("micropython.exe", "queued"),
    ("python.exe", "queued"),
    ("python.exe", "async"),
    ("cpython-venv", "queued"),
    ("cpython-venv", "async"),
]


def _executable_available(key: str, cmd_base: list[str]) -> bool:
    exe = cmd_base[0]
    if key == "cpython-venv":
        return Path(exe).exists()
    return shutil.which(exe) is not None


def _missing_row(interpreter: str, mode: str) -> dict:
    return {
        "interpreter": interpreter,
        "mode": mode,
        "summary": "missing",
        "returncode": -1,
        "timed_out": False,
        "result": None,
        "stdout_tail": "",
        "stderr_tail": "",
    }


def main() -> int:
    rows = []
    for interpreter, mode in DESKTOP_RUNS:
        cmd_base = EXECUTABLES[interpreter]
        if not _executable_available(interpreter, cmd_base):
            print(f"Skipping {interpreter} {mode} (not found: {cmd_base[0]})", file=sys.stderr)
            rows.append(_missing_row(interpreter, mode))
            continue
        print(f"Running {interpreter} {mode}...", file=sys.stderr)
        rows.append(run_case(interpreter, cmd_base, mode, DEFAULT_TIMEOUT, cwd=SRC))

    print()
    print_table(rows, DESKTOP_MODES)

    out_path = REPO / ".cursor" / "desktop_lv_test_results.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(rows, indent=2) + "\n")
    print(f"\nFull results: {out_path}", file=sys.stderr)

    return compute_exit_code(rows, strict_clicks=True)


if __name__ == "__main__":
    sys.exit(main())
