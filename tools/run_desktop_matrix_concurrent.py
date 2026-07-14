#!/usr/bin/env python3
"""Concurrent desktop example matrix (5 runtimes x timer_async 0/1).

Launches up to ``--workers`` example processes at a time. Each case:
  * injects SDL quit after ``--duration-s`` (default 5),
  * is killed if it produces no stdout/stderr within ``--no-output-s`` (default 5).

Usage (from repo root):
  .venv/bin/python tools/run_desktop_matrix_concurrent.py
  .venv/bin/python tools/run_desktop_matrix_concurrent.py --workers 10 --duration-s 5
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
from pathlib import Path
import select
import signal
import subprocess
import sys
import threading
import time

TOOLS = Path(__file__).resolve().parent
REPO = TOOLS.parent
sys.path.insert(0, str(TOOLS))

from example_test_kit import (  # noqa: E402
    SRC,
    WRAPPER,
    example_allowed_on_runtime,
    load_manifest,
    load_runtimes,
    matrix_examples,
    parse_result,
    resolve_runtime_exe,
    runtime_available,
    summarize,
)

DESKTOP_RUNTIMES = (
    "micropython",
    "micropython.exe",
    "circuitpython",
    "cpython-venv",
    "python.exe",
)

# Known missing third-party deps — same skips as prior full-matrix runs.
SKIP_EXAMPLES = frozenset({"micro_gui_simpletest", "touch_gui_simpletest"})

_print_lock = threading.Lock()


def _log(msg: str) -> None:
    with _print_lock:
        print(msg, file=sys.stderr, flush=True)


def _kill_process_group(proc: subprocess.Popen) -> None:
    if proc.poll() is not None:
        return
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError, OSError):
        try:
            proc.kill()
        except OSError:
            pass
    try:
        proc.wait(timeout=2)
    except Exception:
        pass


def run_one(
    *,
    example_id: str,
    example_meta: dict,
    runtime_id: str,
    exe: str,
    timer_async: str,
    duration_s: float,
    no_output_s: float,
    exit_grace_s: float,
) -> dict:
    script = example_meta.get("script", f"examples/{example_id}.py")
    kind = example_meta.get("kind", "loop")
    quit_mode = example_meta.get("quit", "poll")
    bootstrap = example_meta.get("bootstrap", "full")
    wrapper_rel = os.path.relpath(WRAPPER, SRC)
    cmd = [
        exe,
        wrapper_rel,
        example_id,
        "--script",
        script,
        "--kind",
        kind,
        "--quit",
        quit_mode,
        "--bootstrap",
        bootstrap,
        "--duration",
        str(duration_s),
        "--timeout",
        str(duration_s + exit_grace_s),
        "--timer-async",
        str(timer_async),
    ]
    # Windows python.exe under WSL interop block-buffers pipes until exit unless
    # -u is set; PYTHONUNBUFFERED alone is not enough across the Win32 boundary.
    # Without early bytes the no-output watchdog false-kills healthy cases.
    if runtime_id in ("python.exe", "cpython-venv") or os.path.basename(exe) in (
        "python.exe",
        "python",
        "python3",
    ):
        cmd.insert(1, "-u")
    env = os.environ.copy()
    # Timer mode is applied via --timer-async → wrapper env_set (not OS environ).
    env.setdefault("SDL_VIDEODRIVER", "dummy")
    env.setdefault("SDL_AUDIODRIVER", "dummy")
    env.setdefault("PYTHONUNBUFFERED", "1")
    # Early wrapper stderr so the no-output watchdog does not kill healthy
    # examples that only print EXAMPLE_RESULT at exit.
    env.setdefault("PYDISPLAY_TEST_TRACE", "1")

    label = f"{example_id} @ {runtime_id} async={timer_async}"
    _log(f"START {label}")

    t0 = time.monotonic()
    stdout_chunks: list[str] = []
    stderr_chunks: list[str] = []
    saw_output = False
    killed_no_output = False
    timed_out = False

    proc = subprocess.Popen(
        cmd,
        cwd=str(SRC),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        start_new_session=True,
        bufsize=1,
    )
    assert proc.stdout is not None and proc.stderr is not None
    streams = {proc.stdout: stdout_chunks, proc.stderr: stderr_chunks}
    hard_deadline = t0 + duration_s + exit_grace_s

    try:
        while True:
            if proc.poll() is not None and not streams:
                break
            now = time.monotonic()
            if not saw_output and (now - t0) >= no_output_s:
                killed_no_output = True
                _kill_process_group(proc)
                break
            if now >= hard_deadline:
                timed_out = True
                _kill_process_group(proc)
                break

            wait = min(0.2, max(0.05, hard_deadline - now))
            if not saw_output:
                wait = min(wait, max(0.05, no_output_s - (now - t0)))
            ready, _, _ = select.select(list(streams), [], [], wait)
            for fh in ready:
                chunk = fh.read(4096)
                if chunk == "":
                    streams.pop(fh, None)
                    continue
                saw_output = True
                streams[fh].append(chunk)
            if proc.poll() is not None and not ready:
                # Drain remaining buffered output.
                for fh in list(streams):
                    chunk = fh.read()
                    if chunk:
                        saw_output = True
                        streams[fh].append(chunk)
                    streams.pop(fh, None)
                break
    finally:
        if proc.poll() is None:
            _kill_process_group(proc)

    elapsed = time.monotonic() - t0
    stdout = "".join(stdout_chunks)
    stderr = "".join(stderr_chunks)
    returncode = proc.returncode if proc.returncode is not None else -1

    if killed_no_output:
        summary = "hang (no output)"
        result = {
            "example": example_id,
            "status": "hang",
            "error": f"no stdout/stderr within {no_output_s}s",
            "duration_s": duration_s,
        }
    else:
        result = parse_result(stdout)
        summary = summarize(result, returncode, timed_out)

    row = {
        "example": example_id,
        "runtime": runtime_id,
        "timer_async": timer_async,
        "summary": summary,
        "returncode": returncode,
        "timed_out": timed_out or killed_no_output,
        "killed_no_output": killed_no_output,
        "saw_output": saw_output,
        "elapsed_s": round(elapsed, 3),
        "duration_s": duration_s,
        "timeout_s": duration_s + exit_grace_s,
        "result": result,
        "stdout_tail": stdout[-2000:] if stdout else "",
        "stderr_tail": stderr[-1000:] if stderr else "",
    }
    _log(f"DONE  {label} -> {summary} ({elapsed:.1f}s)")
    return row


def build_jobs(
    *,
    all_except_harness: bool,
    only_example: list[str] | None,
) -> list[tuple]:
    runtimes = {k: v for k, v in load_runtimes().items() if k in DESKTOP_RUNTIMES}
    _manifest_defaults, all_examples = load_manifest()
    examples = matrix_examples(
        all_examples,
        only_example,
        all_except_harness=all_except_harness,
    )

    jobs = []
    for timer_async in ("0", "1"):
        for example_id, example_meta in examples.items():
            if example_id in SKIP_EXAMPLES:
                continue
            for runtime_id, runtime_meta in runtimes.items():
                if not example_allowed_on_runtime(example_meta, runtime_id):
                    continue
                if not runtime_available(runtime_id, runtime_meta):
                    continue
                exe = resolve_runtime_exe(runtime_id, runtime_meta)
                if exe is None:
                    continue
                jobs.append((example_id, example_meta, runtime_id, exe, timer_async))
    return jobs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", type=int, default=10)
    parser.add_argument("--duration-s", type=float, default=5.0, help="SDL quit inject delay")
    parser.add_argument(
        "--no-output-s",
        type=float,
        default=5.0,
        help="Kill if no stdout/stderr within this many seconds of launch",
    )
    parser.add_argument(
        "--exit-grace-s",
        type=float,
        default=5.0,
        help="Extra seconds after quit inject for clean exit before hard kill",
    )
    parser.add_argument("--all-except-harness", action="store_true", default=True)
    parser.add_argument("--only-example", nargs="+")
    parser.add_argument(
        "--results-json",
        default=str(REPO / ".cursor" / "example_test_results_desktop_concurrent.json"),
    )
    parser.add_argument(
        "--log",
        default=str(REPO / ".cursor" / "matrix_desktop_concurrent.log"),
    )
    args = parser.parse_args(argv)

    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

    jobs = build_jobs(
        all_except_harness=args.all_except_harness,
        only_example=args.only_example,
    )
    _log(
        f"Queued {len(jobs)} cases "
        f"(5 desktop runtimes x timer_async 0/1, workers={args.workers}, "
        f"quit@{args.duration_s}s, no-output kill@{args.no_output_s}s)"
    )

    rows: list[dict] = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futs = {
            pool.submit(
                run_one,
                example_id=example_id,
                example_meta=example_meta,
                runtime_id=runtime_id,
                exe=exe,
                timer_async=timer_async,
                duration_s=args.duration_s,
                no_output_s=args.no_output_s,
                exit_grace_s=args.exit_grace_s,
            ): (example_id, runtime_id, timer_async)
            for example_id, example_meta, runtime_id, exe, timer_async in jobs
        }
        for fut in as_completed(futs):
            try:
                rows.append(fut.result())
            except Exception as exc:
                example_id, runtime_id, timer_async = futs[fut]
                _log(f"EXC  {example_id} @ {runtime_id} async={timer_async}: {exc}")
                rows.append(
                    {
                        "example": example_id,
                        "runtime": runtime_id,
                        "timer_async": timer_async,
                        "summary": f"error: {exc}",
                        "returncode": -1,
                        "timed_out": False,
                        "killed_no_output": False,
                        "result": None,
                        "stdout_tail": "",
                        "stderr_tail": str(exc),
                    }
                )

    # Stable order for the JSON artifact.
    rows.sort(key=lambda r: (r.get("timer_async", ""), r.get("runtime", ""), r.get("example", "")))
    out = Path(args.results_json)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")

    counts: dict[str, int] = {}
    for r in rows:
        s = r.get("summary") or "?"
        key = "ok" if str(s).endswith(", ok") or s == "ok" else s
        if "ok" in str(s) and "error" not in str(s) and "hang" not in str(s):
            key = "ok"
        elif "hang" in str(s):
            key = "hang"
        elif str(s).startswith("error") or "error" in str(s):
            key = "error"
        else:
            key = str(s)
        counts[key] = counts.get(key, 0) + 1

    _log(f"Wrote {len(rows)} rows -> {out}")
    _log("Counts: " + ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))

    # Also split by mode for familiarity with prior artifacts.
    for mode in ("0", "1"):
        mode_rows = [r for r in rows if str(r.get("timer_async")) == mode]
        mode_out = REPO / ".cursor" / f"example_test_results_desktop_concurrent_async_{mode}.json"
        mode_out.write_text(json.dumps(mode_rows, indent=2) + "\n", encoding="utf-8")
        _log(f"  mode {mode}: {len(mode_rows)} rows -> {mode_out}")

    bad = sum(
        1
        for r in rows
        if "ok" not in str(r.get("summary", ""))
        or "hang" in str(r.get("summary", ""))
        or "error" in str(r.get("summary", ""))
    )
    # Recompute carefully
    bad = 0
    for r in rows:
        s = str(r.get("summary", ""))
        if s.endswith(", ok") or s == "ok":
            continue
        if r.get("result") and r["result"].get("status") == "ok":
            continue
        bad += 1
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
