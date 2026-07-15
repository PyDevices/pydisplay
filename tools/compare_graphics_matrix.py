#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Cross-runtime matrix: native ``graphics`` cmod vs ``src/lib/graphics``.

From repo root::

    python tools/compare_graphics_matrix.py
    python tools/compare_graphics_matrix.py --only-runtime micropython,cpython-venv

For ``cpython-venv`` and ``python.exe``, installs ``graphics-cmod`` from TestPyPI
(first time per interpreter) so ``import graphics`` resolves to the native wheel.

Results: summary table on stderr, JSON at ``.cursor/compare_graphics_results.json``.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

import tomllib

REPO = Path(__file__).resolve().parent.parent
TOOLS = REPO / "tools"
RUNTIMES_TOML = TOOLS / "example_runtimes.toml"
RUN_SCRIPT = TOOLS / "compare_graphics_run.py"
RESULTS_JSON = REPO / ".cursor" / "compare_graphics_results.json"
RESULT_RE = re.compile(r"^GRAPHICS_COMPARE_RESULT=(.+)$", re.MULTILINE)

# Desktop subprocess interpreters that can load graphics cmod alongside staged python.
DEFAULT_RUNTIME_IDS = (
    "micropython",
    "micropython.exe",
    "circuitpython",
    "cpython-venv",
    "python.exe",
)

TESTPYPI_INDEX = os.environ.get("TESTPYPI_INDEX", "https://test.pypi.org/simple/")
PYPI_INDEX = os.environ.get("PYPI_INDEX", "https://pypi.org/simple/")

CPYTHON_RUNTIME_IDS = frozenset({"cpython-venv", "python.exe"})


def load_runtimes() -> dict[str, dict]:
    data = tomllib.loads(RUNTIMES_TOML.read_text(encoding="utf-8"))
    return data.get("runtimes", {})


def _expand_user(path: str) -> str:
    return os.path.expanduser(path)


def resolve_runtime_exe(runtime_id: str, meta: dict) -> str | None:
    command = meta.get("command", [])
    if not command:
        return None

    raw = command[0]
    if raw.startswith("repo:"):
        candidate = REPO / raw.split(":", 1)[1]
        return str(candidate) if candidate.exists() else None

    if raw == ".venv/bin/python":
        candidate = REPO / ".venv" / "bin" / "python"
        return str(candidate) if candidate.exists() else None

    expanded = _expand_user(raw)
    if Path(expanded).exists():
        return expanded

    for rule in meta.get("resolve", []):
        if rule == "PATH":
            found = shutil.which(Path(raw).name)
            if found:
                return found
        elif rule.startswith("~/"):
            candidate = _expand_user(rule)
            if Path(candidate).exists():
                return candidate
        elif rule.startswith("repo:"):
            candidate = REPO / rule.split(":", 1)[1]
            if candidate.exists():
                return str(candidate)

    return shutil.which(Path(raw).name)


def runtime_available(runtime_id: str, meta: dict) -> bool:
    return resolve_runtime_exe(runtime_id, meta) is not None


def _graphics_impl(python_exe: str) -> str | None:
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    proc = subprocess.run(
        [
            python_exe,
            "-c",
            "import graphics; print(graphics.implementation())",
        ],
        cwd=str(REPO),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return None
    return proc.stdout.strip()


def ensure_graphics_cmod(python_exe: str, *, verbose: bool) -> tuple[bool, str]:
    impl = _graphics_impl(python_exe)
    if impl == "native_cmod":
        return True, "graphics-cmod already active"
    if impl == "pydisplay_python":
        if verbose:
            print(
                "Installing graphics-cmod from TestPyPI for {}...".format(python_exe),
                file=sys.stderr,
            )
    elif impl:
        return False, "unexpected graphics implementation: {!r}".format(impl)
    else:
        if verbose:
            print(
                "graphics not importable in {}; installing graphics-cmod...".format(python_exe),
                file=sys.stderr,
            )

    pip = [python_exe, "-m", "pip", "install", "-q", "-U", "pip"]
    subprocess.run(pip, check=True)
    install = [
        python_exe,
        "-m",
        "pip",
        "install",
        "-q",
        "-i",
        TESTPYPI_INDEX,
        "--extra-index-url",
        PYPI_INDEX,
        "graphics-cmod",
    ]
    subprocess.run(install, check=True)

    impl = _graphics_impl(python_exe)
    if impl != "native_cmod":
        return False, "graphics-cmod install failed (implementation={!r})".format(impl)
    return True, "installed graphics-cmod from TestPyPI"


def parse_result(stdout: str) -> dict | None:
    for match in RESULT_RE.finditer(stdout):
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            continue
    return None


def run_case(runtime_id: str, meta: dict, *, verbose: bool, timeout_s: float) -> dict:
    exe = resolve_runtime_exe(runtime_id, meta)
    if not exe:
        return {
            "runtime": runtime_id,
            "status": "skip",
            "summary": "runtime not available",
            "returncode": None,
        }

    setup_note = ""
    if runtime_id in CPYTHON_RUNTIME_IDS:
        ok, setup_note = ensure_graphics_cmod(exe, verbose=verbose)
        if not ok:
            return {
                "runtime": runtime_id,
                "status": "error",
                "summary": setup_note,
                "returncode": 1,
            }

    cmd = [exe, str(RUN_SCRIPT), "--repo", str(REPO), "--quiet"]
    env = os.environ.copy()
    # Avoid repo src/lib shadowing the pip-installed graphics-cmod on CPython.
    env.pop("PYTHONPATH", None)

    t0 = time.monotonic()
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(REPO),
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout_s,
            check=False,
        )
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        proc = exc
        timed_out = True
    elapsed = time.monotonic() - t0

    stdout = proc.stdout if hasattr(proc, "stdout") and proc.stdout else ""
    stderr = proc.stderr if hasattr(proc, "stderr") and proc.stderr else ""
    returncode = proc.returncode if hasattr(proc, "returncode") else 124

    result = parse_result(stdout)
    row = {
        "runtime": runtime_id,
        "exe": exe,
        "returncode": returncode,
        "timed_out": timed_out,
        "duration_s": round(elapsed, 2),
        "setup": setup_note,
        "stdout_tail": stdout[-4000:],
        "stderr_tail": stderr[-4000:],
        "result": result,
    }

    if timed_out:
        row["status"] = "error"
        row["summary"] = "timeout"
        return row

    if result:
        n_err = len(result.get("errors", []))
        n_ok = result.get("checks_passed", 0)
        if result.get("status") == "ok":
            row["status"] = "ok"
            row["summary"] = "{} checks ok".format(n_ok)
        else:
            row["status"] = "error"
            if n_err:
                row["summary"] = "{} fail, first: {}".format(
                    n_err, result.get("errors", [result.get("error")])[0]
                )
            else:
                row["summary"] = result.get("error", "error")
    elif returncode == 0:
        row["status"] = "ok"
        row["summary"] = "ok (no result json)"
    else:
        row["status"] = "error"
        if stdout.strip():
            tail = stdout.strip().splitlines()
        else:
            tail = (stderr or "").strip().splitlines()
        row["summary"] = tail[-1] if tail else "exit {}".format(returncode)

    return row


def print_table(rows: list[dict]) -> None:
    runtimes = [row["runtime"] for row in rows]
    width = max([8, *[len(r) for r in runtimes]])
    print(file=sys.stderr)
    print("{:<{w}} | summary".format("runtime", w=width), file=sys.stderr)
    print("{}-+-{}".format("-" * width, "-" * 60), file=sys.stderr)
    for row in rows:
        print(
            "{:<{w}} | {}".format(row["runtime"], row.get("summary", ""), w=width),
            file=sys.stderr,
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Graphics cmod vs python parity matrix")
    parser.add_argument(
        "--only-runtime",
        help="Comma-separated runtime ids (default: all desktop subprocess runtimes)",
    )
    parser.add_argument("--timeout", type=float, default=120.0, help="Per-runtime timeout seconds")
    parser.add_argument("--verbose", action="store_true", help="Show install/setup notes")
    args = parser.parse_args(argv)

    all_runtimes = load_runtimes()
    if args.only_runtime:
        wanted = [x.strip() for x in args.only_runtime.split(",") if x.strip()]
    else:
        wanted = list(DEFAULT_RUNTIME_IDS)

    rows: list[dict] = []
    for runtime_id in wanted:
        meta = all_runtimes.get(runtime_id)
        if not meta:
            rows.append(
                {
                    "runtime": runtime_id,
                    "status": "skip",
                    "summary": "unknown runtime id",
                }
            )
            continue
        if not runtime_available(runtime_id, meta):
            rows.append(
                {
                    "runtime": runtime_id,
                    "status": "skip",
                    "summary": "not available",
                }
            )
            continue
        if args.verbose:
            print("Running {}...".format(runtime_id), file=sys.stderr)
        rows.append(run_case(runtime_id, meta, verbose=args.verbose, timeout_s=args.timeout))

    RESULTS_JSON.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_JSON.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
    print("Full results: {}".format(RESULTS_JSON), file=sys.stderr)
    print_table(rows)

    failed = [r for r in rows if r.get("status") == "error"]
    return 1 if failed else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        raise SystemExit(130) from None
