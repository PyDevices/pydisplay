#!/usr/bin/env python3
"""Run a pydisplay example immediately and record its desktop window.

Examples:
    python tools/record.py bouncing_balls
    python tools/record.py bouncing_balls 10
    python tools/record.py logo --duration 3 --fps 15 --output demo.mp4
"""

import argparse
import os
from pathlib import Path
import sys
import threading
import time

from screenshot import _prepare_paths, _resolve_example, _run_example


def _default_output(example):
    return Path("docs") / "videos" / f"{Path(example).stem}.mp4"


def _parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("example", help="example name, script path, or importable module")
    parser.add_argument(
        "seconds",
        nargs="?",
        type=float,
        help="recording duration in seconds (default: 5)",
    )
    parser.add_argument("-d", "--duration", type=float, help="same as positional seconds")
    parser.add_argument("--fps", type=int, default=12, help="output frame rate (default: 12)")
    parser.add_argument("-o", "--output", type=Path, help="output MP4 path")
    args = parser.parse_args(argv)
    if args.seconds is not None and args.duration is not None:
        parser.error("use either positional seconds or --duration, not both")
    args.duration = args.duration if args.duration is not None else (args.seconds or 5.0)
    if args.duration <= 0:
        parser.error("duration must be greater than zero")
    if args.fps <= 0:
        parser.error("fps must be greater than zero")
    args.output = args.output or _default_output(args.example)
    return args


def _record_until(deadline, output, fps, state):
    recorder = None
    display_drv = None
    try:
        while time.monotonic() < deadline:
            board_config = sys.modules.get("board_config")
            candidate = getattr(board_config, "display_drv", None)
            if candidate is not None and hasattr(candidate, "open_frame_recorder"):
                display_drv = candidate
                break
            time.sleep(0.01)
        if display_drv is None:
            raise RuntimeError("example did not create a recordable desktop display")

        output.parent.mkdir(parents=True, exist_ok=True)
        recorder = display_drv.open_frame_recorder(str(output), fps=fps)

        # Preserve a frame for one-shot examples that rendered before the
        # recorder was attached. Looping examples add frames from show().
        pixels, _width, _height = display_drv.capture_rgb()
        recorder.write(pixels)

        remaining = deadline - time.monotonic()
        if remaining > 0:
            time.sleep(remaining)
        frames = display_drv.close_frame_recorder()
        recorder = None
        state["message"] = (
            f"saved {output} ({frames} frames at {fps} fps, {type(display_drv).__name__})"
        )
        state["code"] = 0
    except Exception as exc:
        state["message"] = f"recording failed: {type(exc).__name__}: {exc}"
        state["code"] = 1
    finally:
        if recorder is not None:
            try:
                recorder.close()
            except Exception:
                pass
        print(state["message"], flush=True)
        os._exit(state["code"])


def main(argv=None):
    args = _parse_args(argv)
    repo_root = Path(__file__).resolve().parent.parent
    _prepare_paths(repo_root)
    from displaysys._frame_recorder import ffmpeg_executable

    if ffmpeg_executable() is None:
        raise SystemExit("record.py requires ffmpeg on PATH or the imageio-ffmpeg Python package")

    example = _resolve_example(args.example, repo_root)
    output = args.output.resolve()
    os.chdir(repo_root / "src")
    import lib.path  # noqa: F401

    state = {"code": 1, "message": "recording did not run"}
    deadline = time.monotonic() + args.duration
    worker = threading.Thread(
        target=_record_until,
        args=(deadline, output, args.fps, state),
        daemon=True,
    )
    worker.start()
    try:
        _run_example(example)
    except SystemExit as exc:
        if exc.code not in (None, 0):
            raise
    worker.join()
    return state["code"]


if __name__ == "__main__":
    raise SystemExit(main())
