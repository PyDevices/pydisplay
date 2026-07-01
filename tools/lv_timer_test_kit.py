#!/usr/bin/env python3
"""
Run LVGL timer/input harness across desktop Python runtimes.

Subprocesses run ``examples/lv_test_timer_harness.py`` from ``src/`` (~4 s of
checks, then injected ``events.Quit``). Each child prints ``KIT_RESULT=`` on
stdout; exit code 0 is expected on success.

From repo root:
    python tools/lv_timer_test_kit.py
    python tools/lv_timer_test_kit.py --only python.exe no_pump
    python tools/lv_timer_test_kit.py --only cpython-venv --modes pump async

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
NO_LVGL_JSON = REPO / ".cursor" / "comprehensive_timers_no_lvgl_results.json"
DEFAULT_TIMER_PROBE = "multimer.Timer (default)"

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

MODES = ("no_pump", "pump", "async")

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


def _probe_needs_pump_from_stdout(stdout: str) -> bool | None:
    in_default = False
    for line in stdout.splitlines():
        if line.startswith(f"{DEFAULT_TIMER_PROBE}:"):
            in_default = True
            continue
        if in_default:
            m = re.match(r"^\s*NEEDS_PUMP:\s*(True|False)", line)
            if m:
                return m.group(1) == "True"
            if line and not line.startswith(" "):
                break
    return None


def _probe_runtime_needs_pump(runtime_id: str, cmd_base: list[str]) -> bool | None:
    script = (
        "import multimer; "
        "from multimer import Timer; "
        "print('NEEDS_PUMP', getattr(Timer, 'NEEDS_PUMP', False))"
    )
    try:
        proc = subprocess.run(
            [*cmd_base, "-c", script],
            cwd=str(SRC),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=15,
            check=False,
        )
    except (subprocess.TimeoutExpired, OSError):
        return None
    for line in (proc.stdout or "").splitlines():
        if line.startswith("NEEDS_PUMP "):
            return line.split()[-1] == "True"
    return None


def load_default_timer_needs_pump(
    runtimes: tuple[str, ...] | list[str] | None = None,
) -> dict[str, bool | None]:
    """Per-runtime NEEDS_PUMP for ``multimer.Timer`` (default backend)."""
    wanted = tuple(runtimes or LVGL_RUNTIMES)
    out: dict[str, bool | None] = dict.fromkeys(wanted)

    if NO_LVGL_JSON.is_file():
        try:
            rows = json.loads(NO_LVGL_JSON.read_text(encoding="utf-8"))
            for row in rows:
                rt = row.get("runtime")
                if rt not in out:
                    continue
                probe = (row.get("probes") or {}).get(DEFAULT_TIMER_PROBE, {})
                np = probe.get("needs_pump")
                if np is not None:
                    out[rt] = bool(np)
                elif row.get("stdout"):
                    parsed = _probe_needs_pump_from_stdout(row["stdout"])
                    if parsed is not None:
                        out[rt] = parsed
        except (json.JSONDecodeError, OSError):
            pass

    for rt in wanted:
        if out[rt] is not None:
            continue
        cmd = _resolve_command(rt)
        if cmd:
            out[rt] = _probe_runtime_needs_pump(rt, cmd)
    return out


def parse_result(stdout: str) -> dict | None:
    for match in RESULT_RE.finditer(stdout):
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            continue
    return None


def _backend_from_row(row: dict) -> str:
    result = row.get("result")
    if result and result.get("backend"):
        return str(result["backend"])
    stdout = row.get("stdout_tail") or ""
    parsed = parse_result(stdout)
    if parsed and parsed.get("backend"):
        return str(parsed["backend"])
    return "?"


def summarize(  # noqa: PLR0911
    result: dict | None,
    returncode: int,
    timed_out: bool,
    *,
    mode: str = "",
    needs_pump: bool | None = None,
    expected_hang: bool = False,
) -> str:
    if timed_out:
        backend = "?"
        if result and result.get("backend"):
            backend = str(result["backend"])
        if expected_hang or (mode == "no_pump" and needs_pump is True):
            return f"{backend}, hang (expected)"
        return f"{backend}, hang"
    if result is None:
        return "no_result" if returncode == 0 else f"exit_{returncode}"
    status = result.get("status", "?")
    if status == "skip":
        return "NA"
    backend = result.get("backend", "?")
    click = result.get("click_status")
    if mode == "no_pump" and needs_pump is True and status != "ok":
        seconds = int(result.get("seconds", 0))
        if seconds < 2:
            if click == "no timers":
                return f"{backend}, no timers (expected)"
            return f"{backend}, {click or status} (expected)"
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


def _no_pump_expected(needs_pump: bool | None, result: dict | None, timed_out: bool) -> bool:
    if needs_pump is not True:
        return False
    if timed_out:
        return True
    if not result:
        return False
    if result.get("status") == "ok":
        return False
    return int(result.get("seconds", 0)) < 2


def _no_pump_passes(row: dict, needs_pump_map: dict[str, bool | None]) -> bool:
    result = row.get("result")
    if result and result.get("status") == "ok":
        return True
    rt = row["interpreter"]
    needs_pump = needs_pump_map.get(rt)
    return _no_pump_expected(needs_pump, result, bool(row.get("timed_out")))


def _polling_backend(result: dict | None) -> bool:
    if not result:
        return False
    backend = str(result.get("backend", ""))
    return backend in ("_polling", "polling")


def compute_exit_code(
    rows: list[dict],
    *,
    strict_clicks: bool = False,
    needs_pump_map: dict[str, bool | None] | None = None,
) -> int:
    needs_pump_map = needs_pump_map or load_default_timer_needs_pump()
    failed = []
    for row in rows:
        if row.get("summary") == "missing":
            continue
        mode = row.get("mode", "")
        result = row.get("result")

        # pump + async: KIT_RESULT status ok is authoritative (teardown may SIGSEGV)
        if mode in ("pump", "async"):
            passed = (
                result
                and result.get("status") == "ok"
                and not _polling_backend(result)
                and (not strict_clicks or result.get("click_status") == "ok")
            )
            if not passed:
                failed.append(row)
            continue

        if mode == "no_pump":
            if _no_pump_passes(row, needs_pump_map):
                continue
            failed.append(row)
            continue

        failed.append(row)
    return 1 if failed else 0


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
    needs_pump: bool | None = None,
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
    expected_hang = mode == "no_pump" and needs_pump is True
    summary = summarize(
        result,
        returncode,
        timed_out,
        mode=mode,
        needs_pump=needs_pump,
        expected_hang=expected_hang and timed_out,
    )
    if result and result.get("status") == "ok":
        backend = result.get("backend", "?")
        if mode in ("pump", "async") and _polling_backend(result):
            summary = f"{backend}, polling (rejected)"
        else:
            summary = f"{backend}, ok"
    elif mode == "no_pump" and _no_pump_expected(needs_pump, result, timed_out):
        backend = (result or {}).get(
            "backend", _backend_from_row({"result": result, "stdout_tail": stdout})
        )
        if timed_out:
            summary = f"{backend}, hang (expected)"
        elif result and result.get("click_status") == "no timers":
            summary = f"{backend}, no timers (expected)"
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
    needs_pump_map = load_default_timer_needs_pump(tuple(interpreters))
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
            row = run_case(
                name,
                cmd_base,
                mode,
                timeout,
                needs_pump=needs_pump_map.get(name),
            )
            rows.append(row)
            if emit_json:
                print(json.dumps(row, indent=2))

    print()
    print_table(rows, modes_tuple)

    results_path.parent.mkdir(parents=True, exist_ok=True)
    results_path.write_text(json.dumps(rows, indent=2) + "\n")
    print(f"\nFull results: {results_path}", file=sys.stderr)

    return compute_exit_code(rows, strict_clicks=strict_clicks, needs_pump_map=needs_pump_map)


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
        help="Modes to run (default: no_pump pump async)",
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
