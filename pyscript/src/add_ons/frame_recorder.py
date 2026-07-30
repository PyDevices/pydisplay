# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Optional desktop-display video recording support."""


def ffmpeg_executable():
    """Return a system or ``imageio-ffmpeg`` executable, or ``None``."""
    import shutil

    executable = shutil.which("ffmpeg")
    if executable:
        return executable
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except (ImportError, RuntimeError):
        return None


class FFmpegFrameRecorder:
    """Pipe fixed-size RGB24 frames to ffmpeg as an MP4."""

    __slots__ = (
        "_closed",
        "_frame_bytes",
        "_frames",
        "_lock",
        "_next_frame",
        "_proc",
        "fps",
        "height",
        "path",
        "width",
    )

    def __init__(self, path, width, height, fps=12):
        import subprocess
        import threading
        import time

        executable = ffmpeg_executable()
        if executable is None:
            raise RuntimeError(
                "FFmpeg is not available; install imageio-ffmpeg or put ffmpeg on PATH"
            )
        self.path = path
        self.width = width
        self.height = height
        self.fps = fps
        self._frames = 0
        self._closed = False
        self._frame_bytes = width * height * 3
        self._lock = threading.Lock()
        self._next_frame = time.monotonic()
        self._proc = subprocess.Popen(
            [
                executable,
                "-y",
                "-loglevel",
                "error",
                "-f",
                "rawvideo",
                "-pix_fmt",
                "rgb24",
                "-s",
                f"{width}x{height}",
                "-r",
                str(fps),
                "-i",
                "pipe:0",
                "-an",
                "-vf",
                "pad=ceil(iw/2)*2:ceil(ih/2)*2",
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                path,
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )

    def write(self, rgb_bytes):
        import time

        if len(rgb_bytes) != self._frame_bytes:
            raise ValueError(
                f"frame size {len(rgb_bytes)} != expected {self._frame_bytes} "
                f"for {self.width}x{self.height} RGB24"
            )
        with self._lock:
            if self._closed:
                return False
            now = time.monotonic()
            if self._frames and now < self._next_frame:
                return False
            try:
                self._proc.stdin.write(rgb_bytes)
            except BrokenPipeError as exc:
                err = self._proc.stderr.read().decode("utf-8", errors="replace")
                tail = "\n".join(err.strip().splitlines()[-8:])
                raise RuntimeError(f"ffmpeg stopped while recording {self.path}:\n{tail}") from exc
            self._frames += 1
            self._next_frame = now + 1 / self.fps
            return True

    def close(self):
        with self._lock:
            if self._closed:
                return self._frames
            self._closed = True
            try:
                self._proc.stdin.close()
            except Exception:
                pass
            err = self._proc.stderr.read().decode("utf-8", errors="replace")
            try:
                self._proc.stderr.close()
            except Exception:
                pass
            rc = self._proc.wait()
        if rc != 0:
            tail = "\n".join(err.strip().splitlines()[-8:])
            raise RuntimeError(f"ffmpeg exited {rc} for {self.path}:\n{tail}")
        return self._frames
