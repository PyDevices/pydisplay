#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""
Orchestrate car_cluster soak: 5 x N-minute runs with key injection + REPL smoke.

Usage (from repo root)::

    .venv/bin/python tools/car_cluster_soak.py
    SOAK_SECONDS=300 SOAK_RUNS=5 .venv/bin/python tools/car_cluster_soak.py

Fails the process on hang, crash, schedule-queue spam, or missing heartbeats.
"""

from __future__ import annotations

import os
from pathlib import Path
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
WORKER = ROOT / "tools" / "car_cluster_soak_worker.py"
MP = ROOT / "bin" / "micropython"
HB = Path(os.environ.get("SOAK_HEARTBEAT", "/tmp/car_cluster_soak_hb"))
RUNS = int(os.environ.get("SOAK_RUNS", "5"))
SECONDS = int(os.environ.get("SOAK_SECONDS", "300"))
# Heartbeat must refresh at least this often (worker writes ~1 Hz).
HB_STALE_S = float(os.environ.get("SOAK_HB_STALE_S", "20"))
REPL_TIMEOUT_S = float(os.environ.get("SOAK_REPL_TIMEOUT_S", "60"))


def _kill_tree(proc: subprocess.Popen) -> None:
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass


def _repl_smoke(run_id: int) -> None:
    """Import car_cluster under ``micropython -i`` and prove the REPL returns."""
    print(f"[run {run_id}] REPL smoke …", flush=True)
    env = os.environ.copy()
    env.setdefault("SDL_VIDEODRIVER", "dummy")
    env.setdefault("SDL_AUDIODRIVER", "dummy")
    script = (
        "import sys\n"
        "sys.path.insert(0, 'examples')\n"
        "print('REPL_BEFORE')\n"
        "from car_cluster import car_cluster\n"
        "print('REPL_AFTER')\n"
        "import gc\n"
        "print('REPL_MEM', gc.mem_free())\n"
    )
    proc = subprocess.Popen(
        [str(MP), "-i", "lib/path.py"],
        cwd=str(SRC),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=env,
        start_new_session=True,
        bufsize=1,
    )
    assert proc.stdin is not None
    proc.stdin.write(script)
    proc.stdin.flush()
    # Keep stdin open briefly so -i session stays alive after import.
    deadline = time.time() + REPL_TIMEOUT_S
    out_chunks: list[str] = []
    try:
        while time.time() < deadline:
            line = proc.stdout.readline() if proc.stdout else ""
            if line:
                out_chunks.append(line)
                if "REPL_MEM" in line:
                    break
            elif proc.poll() is not None:
                break
            else:
                time.sleep(0.05)
        blob = "".join(out_chunks)
        if "schedule queue full" in blob:
            raise RuntimeError("REPL smoke: schedule queue full\n" + blob[-2000:])
        if "REPL_AFTER" not in blob or "REPL_MEM" not in blob:
            raise RuntimeError(
                f"REPL smoke failed (no REPL_AFTER/MEM within {REPL_TIMEOUT_S}s)\n" + blob[-2000:]
            )
        # Sample CPU briefly — wedged runs sit near 100%.
        time.sleep(2.0)
        cpu = _cpu_pct(proc.pid)
        print(f"[run {run_id}] REPL ok cpu≈{cpu:.0f}%", flush=True)
        if cpu > 70:
            raise RuntimeError(f"REPL smoke: CPU too high after idle ({cpu:.0f}%)")
    finally:
        _kill_tree(proc)
        try:
            proc.wait(timeout=3)
        except Exception:
            pass


def _cpu_pct(pid: int) -> float:
    try:
        out = subprocess.check_output(["ps", "-o", "pcpu=", "-p", str(pid)], text=True).strip()
        # Child micropython may be in the process group; sample group members.
        if not out:
            return 0.0
        return float(out.split()[0])
    except Exception:
        return 0.0


def _soak_once(run_id: int) -> None:
    print(f"[run {run_id}] soak {SECONDS}s …", flush=True)
    if HB.exists():
        HB.unlink()
    env = os.environ.copy()
    env.setdefault("SDL_VIDEODRIVER", "dummy")
    env.setdefault("SDL_AUDIODRIVER", "dummy")
    env["SOAK_SECONDS"] = str(SECONDS)
    env["SOAK_HEARTBEAT"] = str(HB)
    env["SOAK_RUN_ID"] = str(run_id)

    log_path = Path(f"/tmp/car_cluster_soak_run{run_id}.log")
    log_f = open(log_path, "w")  # noqa: SIM115 — handed to Popen; closed in finally
    proc = subprocess.Popen(
        [str(MP), str(WORKER)],
        cwd=str(SRC),
        stdin=subprocess.DEVNULL,
        stdout=log_f,
        stderr=subprocess.STDOUT,
        env=env,
        start_new_session=True,
    )
    t0 = time.time()
    last_hb_mtime = 0.0
    last_hb_ok = t0
    try:
        while True:
            now = time.time()
            elapsed = now - t0
            rc = proc.poll()
            if HB.exists():
                mtime = HB.stat().st_mtime
                if mtime != last_hb_mtime:
                    last_hb_mtime = mtime
                    last_hb_ok = now
            if rc is not None:
                log_f.flush()
                text = log_path.read_text(errors="replace")
                if rc != 0 and "SOAK_DONE" not in text:
                    raise RuntimeError(f"soak run {run_id} exited rc={rc}\n" + text[-3000:])
                if "schedule queue full" in text:
                    raise RuntimeError(f"soak run {run_id}: schedule queue full\n" + text[-3000:])
                if "SOAK_DONE" not in text:
                    raise RuntimeError(f"soak run {run_id}: missing SOAK_DONE\n" + text[-3000:])
                print(
                    f"[run {run_id}] soak ok elapsed={elapsed:.0f}s log={log_path}",
                    flush=True,
                )
                return
            if elapsed > SECONDS + 60:
                raise RuntimeError(f"soak run {run_id}: overrun ({elapsed:.0f}s)")
            if now - last_hb_ok > HB_STALE_S and elapsed > 15:
                raise RuntimeError(
                    f"soak run {run_id}: heartbeat stale ({now - last_hb_ok:.0f}s) — likely wedged"
                )
            # Spot-check CPU after warmup
            if elapsed > 30 and int(elapsed) % 30 < 2:
                cpu = _cpu_pct(proc.pid)
                # Also check children
                try:
                    kids = subprocess.check_output(
                        ["pgrep", "-P", str(proc.pid)], text=True
                    ).split()
                    for k in kids:
                        cpu = max(cpu, _cpu_pct(int(k)))
                except Exception:
                    pass
                if cpu > 85:
                    raise RuntimeError(
                        f"soak run {run_id}: CPU pegged ({cpu:.0f}%) — likely wedged"
                    )
            time.sleep(1.0)
    finally:
        if proc.poll() is None:
            _kill_tree(proc)
            try:
                proc.wait(timeout=5)
            except Exception:
                pass
        log_f.close()


def main() -> int:
    if not MP.is_file():
        print(f"missing micropython binary: {MP}", file=sys.stderr)
        return 2
    print(f"car_cluster soak: runs={RUNS} seconds={SECONDS} mp={MP}", flush=True)
    for i in range(1, RUNS + 1):
        _repl_smoke(i)
        _soak_once(i)
    print("ALL SOAK RUNS PASSED", flush=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"SOAK FAILED: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
