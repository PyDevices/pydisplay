#!/usr/bin/env python3
"""
Run displaysys_deinit_test on all desktop Python executables.

From repo root:
    python tools/run_display_teardown_tests.py
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "src"
HARNESS = "examples/displaysys_deinit_test.py"
DEFAULT_TIMEOUT = 15

EXECUTABLES: dict[str, str] = {
    "micropython": os.path.expanduser("~/bin/micropython"),
    "circuitpython": os.path.expanduser("~/bin/circuitpython"),
    "micropython.exe": os.path.expanduser("~/bin/micropython.exe"),
    "python.exe": os.path.expanduser("~/bin/python.exe"),
    "pydisplay-venv": os.path.expanduser("~/github/pydisplay/.venv/bin/python"),
}


def _resolve_exe(path: str) -> str | None:
    p = Path(path)
    if p.exists():
        return str(p)
    return shutil.which(p.name)


def _missing_row(interpreter: str) -> dict:
    return {
        "interpreter": interpreter,
        "summary": "missing",
        "returncode": -1,
        "timed_out": False,
        "stdout_tail": "",
        "stderr_tail": "",
    }


def run_one(interpreter: str, exe: str) -> dict:
    cmd = [exe, HARNESS]
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(SRC),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=DEFAULT_TIMEOUT,
            check=False,
        )
        stdout = proc.stdout or ""
        stderr = proc.stderr or ""
        ok = proc.returncode == 0 and "DEINIT_OK" in stdout
        if ok:
            summary = "ok"
        elif proc.returncode != 0:
            summary = f"exit_{proc.returncode}"
        else:
            summary = "no_deinit_ok"
        return {
            "interpreter": interpreter,
            "summary": summary,
            "returncode": proc.returncode,
            "timed_out": False,
            "stdout_tail": stdout[-500:],
            "stderr_tail": stderr[-500:],
        }
    except subprocess.TimeoutExpired as exc:
        stdout = (exc.stdout or "") if isinstance(exc.stdout, str) else ""
        stderr = (exc.stderr or "") if isinstance(exc.stderr, str) else ""
        return {
            "interpreter": interpreter,
            "summary": "timeout",
            "returncode": -1,
            "timed_out": True,
            "stdout_tail": stdout[-500:] if stdout else "",
            "stderr_tail": stderr[-500:] if stderr else "",
        }


def _print_table(rows: list[dict]) -> None:
    flavor_w = max(16, max(len(r["interpreter"]) for r in rows) + 2)
    print(f"{'interpreter':<{flavor_w}} | summary")
    print("-" * flavor_w + "-+-" + "-" * 20)
    for row in rows:
        print(f"{row['interpreter']:<{flavor_w}} | {row['summary']}")


def _compute_exit_code(rows: list[dict]) -> int:
    for row in rows:
        if row["summary"] not in ("ok", "missing"):
            return 1
    return 0


def main() -> int:
    rows = []
    for interpreter, path in EXECUTABLES.items():
        exe = _resolve_exe(path)
        if exe is None:
            print(f"Skipping {interpreter} (not found: {path})", file=sys.stderr)
            rows.append(_missing_row(interpreter))
            continue
        print(f"Running {interpreter} ({exe})...", file=sys.stderr)
        rows.append(run_one(interpreter, exe))

    print()
    _print_table(rows)

    out_path = REPO / ".cursor" / "display_teardown_test_results.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(rows, indent=2) + "\n")
    print(f"\nFull results: {out_path}", file=sys.stderr)

    return _compute_exit_code(rows)


if __name__ == "__main__":
    sys.exit(main())
