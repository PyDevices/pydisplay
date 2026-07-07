#!/usr/bin/env python3
"""
Run the LVGL timer/input harness across desktop Python runtimes.

Subprocesses run ``examples/lv_test_timer_harness.py`` from ``src/`` (~4 s of
checks, then an injected ``events.Quit``). Each child prints ``KIT_RESULT=`` on
stdout; exit code 0 is expected on success.

The board's shared broker timer drives LVGL (``multimer.Timer`` never needs
"pumping"), so there is no pump/no_pump distinction: the only modes are ``sync``
and ``async``.

From repo root:
    python tools/lv_timer_test_kit.py
    python tools/lv_timer_test_kit.py --only cpython-venv
    python tools/lv_timer_test_kit.py --only cpython-venv --modes async

Runtimes resolve via ``tools/example_runtimes.toml`` (same as example_test_kit).
Missing executables show as ``missing`` in the table.
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
TOOLS = REPO / "tools"
HARNESS_ARG = "examples/lv_test_timer_harness.py"
RESULT_RE = re.compile(r"^KIT_RESULT=(.+)$", re.MULTILINE)
DEFAULT_TIMEOUT = 45
DEFAULT_RESULTS = REPO / ".cursor" / "lv_timer_test_kit_results.json"

# Subprocess LVGL matrix (order: Unix first, then Windows .exe targets).
LVGL_RUNTIMES = (
    "micropython",
    "circuitpython",
    "cpython-venv",
    "micropython.exe",
    "python.exe",
)

# Back-compat alias for docs/CLI that used ``cpython``.
RUNTIME_ALIASES = {"cpython": "cpython-venv"}

MODES = ("sync", "async")

sys.path.insert(0, str(TOOLS))
from example_test_kit import load_runtimes, resolve_runtime_exe  # noqa: E402


def _normalize_runtime(name: str) -> str:
    return RUNTIME_ALIASES.get(name, name)


def _runtime_choices() -> list[str]:
    return sorted(set(LVGL_RUNTIMES) | set(RUNTIME_ALIASES))


def _resolve_command(runtime_id: str) -> list[str] | None:
    meta = load_runtimes().get(runtime_id)
    if not meta:
        return None
    exe = resolve_runtime_exe(runtime_id, meta)
    return [exe] if exe else None


def _resolve_interpreters(only: list[str] | None) -> dict[str, list[str] | None]:
    selected = [_normalize_runtime(n) for n in (only or LVGL_RUNTIMES)]
    out: dict[str, list[str] | None] = {}
    for name in selected:
        if name not in LVGL_RUNTIMES:
            print(f"Unknown interpreter {name!r}", file=sys.stderr)
            sys.exit(2)
        out[name] = _resolve_command(name)
    return out


def load_default_timer_needs_pump(
    runtimes: tuple[str, ...] | list[str] | None = None,
) -> dict[str, bool]:
    """Compatibility shim: ``multimer.Timer`` never needs pumping now (all False).

    Kept so older report tools that still import this keep working.
    """
    wanted = tuple(runtimes or LVGL_RUNTIMES)
    return dict.fromkeys(wanted, False)


def parse_result(stdout: str) -> dict | None:
    for match in RESULT_RE.finditer(stdout):
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            continue
    return None


def summarize(result: dict | None, returncode: int, timed_out: bool) -> str:
    if timed_out:
        backend = (result or {}).get("backend", "?")
        return f"{backend}, hang"
    if result is None:
        return "no_result" if returncode == 0 else f"exit_{returncode}"
    status = result.get("status", "?")
    backend = result.get("backend", "?")
    if status == "skip":
        return "NA"
    if status == "ok":
        return f"{backend}, ok"
    if status == "error":
        return f"{backend}, error"
    click = result.get("click_status")
    return f"{backend}, {click or status}"


def compute_exit_code(
    rows: list[dict],
    *,
    strict_clicks: bool = False,
    needs_pump_map: dict[str, bool | None] | None = None,
) -> int:
    for row in rows:
        if row.get("summary") == "missing":
            continue
        if row.get("timed_out"):
            return 1
        result = row.get("result")
        ok = bool(result) and result.get("status") == "ok"
        if strict_clicks:
            ok = ok and result.get("click_status") == "ok"
        if not ok:
            return 1
    return 0


def _missing_row(interpreter: str, mode: str, *, exe_hint: str = "") -> dict:
    return {
        "interpreter": interpreter,
        "mode": mode,
        "summary": "missing",
        "returncode": -1,
        "timed_out": False,
        "result": None,
        "stdout_tail": "",
        "stderr_tail": exe_hint,
    }


def run_case(
    interpreter: str,
    cmd_base: list[str],
    mode: str,
    timeout: int = DEFAULT_TIMEOUT,
    *,
    cwd: Path | None = None,
    needs_pump: bool | None = None,  # accepted for backward compat; unused
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
    flavors = []
    seen = set()
    for r in rows:
        name = r["interpreter"]
        if name not in seen:
            flavors.append(name)
            seen.add(name)
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


def run_kit(
    *,
    only: list[str] | None = None,
    modes: tuple[str, ...] | list[str] = MODES,
    timeout: int = DEFAULT_TIMEOUT,
    strict_clicks: bool = False,
    results_path: Path = DEFAULT_RESULTS,
    emit_json: bool = False,
) -> int:
    modes_tuple = tuple(modes)
    interpreters = _resolve_interpreters(only)
    rows = []
    for name, cmd_base in interpreters.items():
        for mode in modes_tuple:
            if cmd_base is None:
                meta = load_runtimes().get(name, {})
                hint = (meta.get("command") or ["?"])[0]
                print(f"Skipping {name} {mode} (not found: {hint})", file=sys.stderr)
                rows.append(_missing_row(name, mode, exe_hint=hint))
                continue
            print(f"Running {name} {mode}...", file=sys.stderr)
            row = run_case(name, cmd_base, mode, timeout)
            rows.append(row)
            if emit_json:
                print(json.dumps(row, indent=2))

    print()
    print_table(rows, modes_tuple)

    results_path.parent.mkdir(parents=True, exist_ok=True)
    results_path.write_text(json.dumps(rows, indent=2) + "\n")
    print(f"\nFull results: {results_path}", file=sys.stderr)

    return compute_exit_code(rows, strict_clicks=strict_clicks)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="LVGL timer test kit runner")
    parser.add_argument(
        "--only",
        nargs="+",
        choices=_runtime_choices(),
        metavar="RUNTIME",
        help="Run subset of runtimes (default: all LVGL subprocess targets)",
    )
    parser.add_argument(
        "--modes",
        nargs="+",
        choices=list(MODES),
        default=list(MODES),
        help="Modes to run (default: sync async)",
    )
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    parser.add_argument(
        "--strict-clicks",
        action="store_true",
        help="Fail when click_status is not ok (desktop LVGL policy)",
    )
    parser.add_argument("--json", action="store_true", help="Print full JSON per run")
    args = parser.parse_args(argv)

    return run_kit(
        only=args.only,
        modes=args.modes,
        timeout=args.timeout,
        strict_clicks=args.strict_clicks,
        emit_json=args.json,
    )


if __name__ == "__main__":
    sys.exit(main())
