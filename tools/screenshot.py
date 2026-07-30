#!/usr/bin/env python3
"""Run a pydisplay example and save its desktop window as a PNG.

Examples:
    python tools/screenshot.py hello.py
    python tools/screenshot.py bouncing_balls 3
    python tools/screenshot.py logo --delay 2 --output logo.png
"""

import argparse
import binascii
import os
from pathlib import Path
import runpy
import struct
import sys
import threading
import time
import zlib


def _png_chunk(kind, data):
    payload = kind + data
    return struct.pack(">I", len(data)) + payload + struct.pack(">I", binascii.crc32(payload))


def save_rgb_png(path, pixels, width, height):
    """Write packed top-to-bottom RGB24 pixels as a PNG without Pillow."""
    stride = width * 3
    if len(pixels) != stride * height:
        raise ValueError(
            f"RGB buffer has {len(pixels)} bytes; expected {stride * height} for {width}x{height}"
        )
    rows = bytearray()
    for y in range(height):
        rows.append(0)
        start = y * stride
        rows.extend(pixels[start : start + stride])
    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as stream:
        stream.write(b"\x89PNG\r\n\x1a\n")
        stream.write(_png_chunk(b"IHDR", header))
        stream.write(_png_chunk(b"IDAT", zlib.compress(rows)))
        stream.write(_png_chunk(b"IEND", b""))


def _default_output(example):
    return Path("docs") / "screenshots" / f"{Path(example).stem}.png"


def _resolve_example(example, repo_root):
    path = Path(example)
    candidates = (path, repo_root / "src" / "examples" / path)
    if not path.suffix:
        candidates += (repo_root / "src" / "examples" / f"{example}.py",)
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    return example


def _parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("example", help="example script path or importable module name")
    parser.add_argument(
        "seconds",
        nargs="?",
        type=float,
        help="seconds to wait before capture (default: 1)",
    )
    parser.add_argument("-d", "--delay", type=float, help="same as positional seconds")
    parser.add_argument("-o", "--output", type=Path, help="output PNG path")
    args = parser.parse_args(argv)
    if args.seconds is not None and args.delay is not None:
        parser.error("use either positional seconds or --delay, not both")
    args.delay = args.delay if args.delay is not None else (args.seconds or 1.0)
    if args.delay < 0:
        parser.error("delay must not be negative")
    args.output = args.output or _default_output(args.example)
    return args


def _prepare_paths(repo_root):
    src = repo_root / "src"
    tools = repo_root / "tools"
    for path in (str(tools), str(src), str(src / "lib")):
        if path not in sys.path:
            sys.path.insert(0, path)
    import sibling_repos

    sibling_repos.prepend_sibling_sys_path(repo_root=str(repo_root))


def _run_example(example):
    if isinstance(example, Path):
        runpy.run_path(str(example), run_name="__main__")
    else:
        runpy.run_module(example, run_name="__main__", alter_sys=True)


def _capture_after(delay, output, state):
    time.sleep(delay)
    try:
        board_config = sys.modules.get("board_config")
        if board_config is None:
            raise RuntimeError("example did not import board_config before the capture deadline")
        display_drv = board_config.display_drv

        capture = getattr(display_drv, "capture_rgb", None)
        if capture is None:
            raise RuntimeError(
                f"{type(display_drv).__name__} does not support desktop screenshots"
            )
        pixels, width, height = capture()
        save_rgb_png(output, pixels, width, height)
        state["message"] = f"saved {output} ({width}x{height}, {type(display_drv).__name__})"
        state["code"] = 0
    except Exception as exc:
        state["message"] = f"screenshot failed: {type(exc).__name__}: {exc}"
        state["code"] = 1
    finally:
        print(state["message"], flush=True)
        os._exit(state["code"])


def main(argv=None):
    args = _parse_args(argv)
    repo_root = Path(__file__).resolve().parent.parent
    _prepare_paths(repo_root)
    example = _resolve_example(args.example, repo_root)
    output = args.output.resolve()
    os.chdir(repo_root / "src")
    import lib.path  # noqa: F401

    state = {"code": 1, "message": "screenshot did not run"}
    worker = threading.Thread(
        target=_capture_after,
        args=(args.delay, output, state),
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
