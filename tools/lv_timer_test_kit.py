#!/usr/bin/env python3
"""
Run LVGL timer/input harness across MicroPython, CircuitPython, and CPython.

From repo root:
    python tools/lv_timer_test_kit.py
    python tools/lv_timer_test_kit.py --only cpython sync
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "src"
HARNESS = SRC / "examples" / "lv_test_timer_harness.py"
HARNESS_ARG = "examples/lv_test_timer_harness.py"
RESULT_RE = re.compile(r"^KIT_RESULT=(.+)$", re.MULTILINE)
DEFAULT_TIMEOUT = 45

INTERPRETERS = {
    "micropython": ["micropython"],
    "circuitpython": ["circuitpython"],
    "cpython": [str(REPO / ".venv" / "bin" / "python")],
}

MODES = ("sync", "queued", "async")


def _resolve_interpreters(only: list[str] | None) -> dict[str, list[str]]:
    selected = only or list(INTERPRETERS)
    out = {}
    for name in selected:
        if name not in INTERPRETERS:
            print(f"Unknown interpreter {name!r}", file=sys.stderr)
            sys.exit(2)
        exe = INTERPRETERS[name][0]
        if not Path(exe).exists() and name == "cpython":
            print(f"CPython venv not found: {exe}", file=sys.stderr)
            print("Create repo-root .venv: python3 -m venv .venv", file=sys.stderr)
            sys.exit(2)
        out[name] = INTERPRETERS[name]
    return out


def parse_result(stdout: str) -> dict | None:
    for match in RESULT_RE.finditer(stdout):
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            continue
    return None


def summarize(result: dict | None, returncode: int, timed_out: bool) -> str:
    if timed_out:
        return "hang"
    if result is None:
        return "no_result" if returncode == 0 else f"exit_{returncode}"
    status = result.get("status", "?")
    if status == "skip":
        return "NA"
    backend = result.get("backend", "?")
    click = result.get("click_status")
    if click:
        if click == "ok":
            return f"{backend}, ok"
        if click == "no manual clicks":
            return f"{backend}, no clicks"
        if click == "no click count":
            return f"{backend}, no click count"
        if click == "no timers":
            return f"{backend}, no timers"
        return f"{backend}, {click}"
    seconds = result.get("seconds", 0)
    taps = result.get("taps", 0)
    if status == "error":
        return f"{backend}, error"
    if seconds < 2:
        return f"{backend}, no timers"
    if taps < 1:
        return f"{backend}, no clicks"
    return f"{backend}, ok"


def compute_exit_code(rows: list[dict], *, strict_clicks: bool = False) -> int:
    failed = []
    for row in rows:
        if row.get("summary") == "missing":
            continue
        if row["timed_out"] or row["summary"].startswith("exit_") or row["summary"] == "no_result":
            failed.append(row)
            continue
        result = row.get("result")
        if not result:
            failed.append(row)
            continue
        if result.get("status") == "skip":
            continue
        if result.get("status") == "error":
            failed.append(row)
            continue
        if result.get("seconds", 0) < 2 and result.get("status") != "skip":
            failed.append(row)
            continue
        if strict_clicks and result.get("click_status") != "ok":
            failed.append(row)
            continue
        if not strict_clicks and (
            row["summary"].endswith(", no timers") or row["summary"].endswith(", error")
        ):
            failed.append(row)
    return 1 if failed else 0


def run_case(
    interpreter: str,
    cmd_base: list[str],
    mode: str,
    timeout: int = DEFAULT_TIMEOUT,
    *,
    cwd: Path | None = None,
) -> dict:
    cmd = [*cmd_base, HARNESS_ARG, mode]
    env = os.environ.copy()
    run_cwd = str(cwd or SRC)
    try:
        proc = subprocess.run(
            cmd,
            cwd=run_cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            env=env,
            check=False,
        )
        timed_out = False
        returncode = proc.returncode
        stdout = proc.stdout or ""
        stderr = proc.stderr or ""
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        returncode = -1
        stdout = (exc.stdout or "") if isinstance(exc.stdout, str) else ""
        stderr = (exc.stderr or "") if isinstance(exc.stderr, str) else ""

    result = parse_result(stdout)
    summary = summarize(result, returncode, timed_out)
    return {
        "interpreter": interpreter,
        "mode": mode,
        "summary": summary,
        "returncode": returncode,
        "timed_out": timed_out,
        "result": result,
        "stdout_tail": stdout[-2000:] if stdout else "",
        "stderr_tail": stderr[-1000:] if stderr else "",
    }


def print_table(rows: list[dict], modes: tuple[str, ...] = MODES):
    flavors = sorted({r["interpreter"] for r in rows})
    col_w = max(8, max(len(m) for m in modes) + 2)
    flavor_w = max(12, max(len(f) for f in flavors) + 2)

    header = f"{'flavor':<{flavor_w}} |" + "|".join(f"{m:<{col_w}}" for m in modes)
    sep = "-" * flavor_w + "-+-" + "-+-".join("-" * col_w for _ in modes)
    print(header)
    print(sep)

    by_key = {(r["interpreter"], r["mode"]): r["summary"] for r in rows}
    for flavor in flavors:
        cells = [f"{flavor:<{flavor_w}}"]
        for mode in modes:
            cells.append(f"{by_key.get((flavor, mode), '—'):<{col_w}}")
        print(" |".join(cells))


def main():
    parser = argparse.ArgumentParser(description="LVGL timer test kit runner")
    parser.add_argument(
        "--only",
        nargs="+",
        choices=list(INTERPRETERS),
        help="Run subset of interpreters (default: all available)",
    )
    parser.add_argument(
        "--modes",
        nargs="+",
        choices=list(MODES),
        default=list(MODES),
        help="Modes to run (default: sync queued async)",
    )
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    parser.add_argument("--json", action="store_true", help="Print full JSON results")
    args = parser.parse_args()

    interpreters = _resolve_interpreters(args.only)
    rows = []
    for name, cmd_base in interpreters.items():
        for mode in args.modes:
            print(f"Running {name} {mode}...", file=sys.stderr)
            row = run_case(name, cmd_base, mode, args.timeout)
            rows.append(row)
            if args.json:
                print(json.dumps(row, indent=2))

    print()
    print_table(rows, tuple(args.modes))

    out_path = REPO / ".cursor" / "lv_timer_test_kit_results.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(rows, indent=2) + "\n")
    print(f"\nFull results: {out_path}", file=sys.stderr)

    return compute_exit_code(rows, strict_clicks=False)


if __name__ == "__main__":
    sys.exit(main())
