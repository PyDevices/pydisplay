"""
Pipe pygame frames to ffmpeg for tower_climb recordings.

Set ``TOWER_CLIMB_VIDEO`` to an output ``.mp4`` path.  Each call to
``grab()`` after ``display_drv.show()`` becomes one encoded frame at
``TOWER_CLIMB_VIDEO_FPS`` (default 12).
"""

import os
import subprocess

_capture = None


def _surface_rgb(surf):
    import pygame as pg

    if hasattr(pg.image, "tostring"):
        return pg.image.tostring(surf, "RGB")
    return pg.image.tobytes(surf, "RGB")


class _VideoCapture:
    __slots__ = ("_proc", "_closed", "path", "frames")

    def __init__(self, path, fps):
        import pygame as pg

        surf = pg.display.get_surface()
        if surf is None:
            raise RuntimeError("no pygame display surface for video capture")
        w, h = surf.get_size()
        self.path = path
        self.frames = 0
        self._closed = False
        self._proc = subprocess.Popen(
            [
                "ffmpeg",
                "-y",
                "-f",
                "rawvideo",
                "-pix_fmt",
                "rgb24",
                "-s",
                f"{w}x{h}",
                "-r",
                str(fps),
                "-i",
                "pipe:0",
                "-an",
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

    def grab(self):
        import pygame as pg

        if self._closed:
            return
        surf = pg.display.get_surface()
        if surf is None:
            return
        self._proc.stdin.write(_surface_rgb(surf))
        self.frames += 1

    def close(self):
        if self._closed:
            return
        self._closed = True
        try:
            self._proc.stdin.close()
        except Exception:
            pass
        err = self._proc.stderr.read().decode("utf-8", errors="replace")
        rc = self._proc.wait()
        if rc != 0:
            tail = "\n".join(err.strip().splitlines()[-8:])
            raise RuntimeError(f"ffmpeg exited {rc} for {self.path}:\n{tail}")


def open_capture():
    global _capture
    path = os.environ.get("TOWER_CLIMB_VIDEO", "").strip()
    if not path:
        return None
    fps = int(os.environ.get("TOWER_CLIMB_VIDEO_FPS", "12"))
    _capture = _VideoCapture(path, fps)
    return _capture


def grab():
    if _capture is not None:
        _capture.grab()


def close():
    global _capture
    if _capture is None:
        return
    try:
        _capture.close()
    finally:
        _capture = None


def active():
    return _capture is not None
